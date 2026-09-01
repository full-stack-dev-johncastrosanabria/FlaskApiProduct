import json

import pytest

from app.database import db
from app.models import Category, Product


class TestProducts:
    """Tests para endpoints de productos"""
    
    @pytest.fixture(autouse=True)
    def setup(self, client, app):
        """Setup para crear categorías de prueba"""
        with app.app_context():
            # Crear categorías de prueba
            cat1 = Category(name='electrónica', description='Productos electrónicos')
            cat2 = Category(name='accesorios', description='Accesorios')
            cat3 = Category(name='test', description='Categoría de prueba')
            db.session.add_all([cat1, cat2, cat3])
            db.session.commit()
            self.cat1_id = cat1.id
            self.cat2_id = cat2.id
            self.cat3_id = cat3.id
    
    def test_get_products_empty(self, client):
        """Test obtener productos cuando no hay ninguno"""
        response = client.get('/api/products')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 0
        assert data['data'] == []
    
    def test_create_product_success(self, client):
        """Test crear producto exitosamente"""
        product_data = {
            'name': 'Laptop',
            'price': 999.99,
            'category_id': self.cat1_id,
            'description': 'Laptop de alta gama',
            'stock': 10
        }
        response = client.post(
            '/api/products',
            data=json.dumps(product_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['name'] == 'Laptop'
        assert data['data']['price'] == 999.99
        assert 'id' in data['data']
    
    def test_create_product_missing_fields(self, client):
        """Test crear producto sin campos requeridos"""
        product_data = {'name': 'Laptop'}
        response = client.post(
            '/api/products',
            data=json.dumps(product_data),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_create_product_invalid_price(self, client):
        """Test crear producto con precio inválido"""
        product_data = {
            'name': 'Laptop',
            'price': -10,
            'category_id': self.cat1_id
        }
        response = client.post(
            '/api/products',
            data=json.dumps(product_data),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'precio' in data['error'].lower() or 'price' in data['error'].lower()
    
    def test_get_product_by_id(self, client):
        """Test obtener producto por ID"""
        # Crear producto
        product_data = {
            'name': 'Mouse',
            'price': 25.99,
            'category_id': self.cat2_id
        }
        create_response = client.post(
            '/api/products',
            data=json.dumps(product_data),
            content_type='application/json'
        )
        product_id = json.loads(create_response.data)['data']['id']
        
        # Obtener producto
        response = client.get(f'/api/products/{product_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == product_id
    
    def test_update_product(self, client):
        """Test actualizar producto"""
        # Crear producto
        product_data = {
            'name': 'Mouse',
            'price': 25.99,
            'category_id': self.cat2_id
        }
        create_response = client.post(
            '/api/products',
            data=json.dumps(product_data),
            content_type='application/json'
        )
        product_id = json.loads(create_response.data)['data']['id']
        
        # Actualizar producto
        update_data = {'price': 29.99, 'stock': 50}
        response = client.put(
            f'/api/products/{product_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['price'] == 29.99
        assert data['data']['stock'] == 50
    
    def test_delete_product(self, client):
        """Test eliminar producto"""
        # Crear producto
        product_data = {
            'name': 'Mouse',
            'price': 25.99,
            'category_id': self.cat2_id
        }
        create_response = client.post(
            '/api/products',
            data=json.dumps(product_data),
            content_type='application/json'
        )
        product_id = json.loads(create_response.data)['data']['id']
        
        # Eliminar producto
        response = client.delete(f'/api/products/{product_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verificar que ya no existe
        get_response = client.get(f'/api/products/{product_id}')
        assert get_response.status_code == 404
    
    def test_filter_products_by_price(self, client):
        """Test filtrar productos por precio"""
        # Crear productos con diferentes precios
        products = [
            {'name': 'Producto 1', 'price': 10.0, 'category_id': self.cat3_id},
            {'name': 'Producto 2', 'price': 25.0, 'category_id': self.cat3_id},
            {'name': 'Producto 3', 'price': 50.0, 'category_id': self.cat3_id}
        ]
        for product in products:
            client.post(
                '/api/products',
                data=json.dumps(product),
                content_type='application/json'
            )
        
        # Filtrar por precio mínimo
        response = client.get('/api/products?min_price=20')
        data = json.loads(response.data)
        assert data['count'] == 2
        
        # Filtrar por precio máximo
        response = client.get('/api/products?max_price=30')
        data = json.loads(response.data)
        assert data['count'] == 2
        
        # Filtrar por rango
        response = client.get('/api/products?min_price=20&max_price=40')
        data = json.loads(response.data)
        assert data['count'] == 1
    
    def test_filter_products_by_category(self, client):
        """Test filtrar productos por categoría"""
        # Crear productos con diferentes categorías
        products = [
            {'name': 'Laptop', 'price': 999.99, 'category_id': self.cat1_id},
            {'name': 'Mouse', 'price': 25.99, 'category_id': self.cat2_id},
            {'name': 'Teclado', 'price': 49.99, 'category_id': self.cat2_id}
        ]
        for product in products:
            client.post(
                '/api/products',
                data=json.dumps(product),
                content_type='application/json'
            )
        
        # Filtrar por categoría (por nombre)
        response = client.get('/api/products?category=accesorios')
        data = json.loads(response.data)
        assert data['count'] == 2


class TestLowStockEndpoint:
    """Tests para GET /api/products/low-stock"""

    @pytest.fixture(autouse=True)
    def setup(self, app):
        """Setup para crear productos de prueba con costos y stocks variados"""
        with app.app_context():
            # Crear categoría de prueba
            cat = Category(name='test_low_stock', description='Categoría para low-stock tests')
            db.session.add(cat)
            db.session.commit()
            self.cat_id = cat.id

    def _create_products(self, products_data):
        db.session.add_all(Product(**data) for data in products_data)
        db.session.commit()

    @staticmethod
    def _forbid_product_query(monkeypatch):
        class ForbiddenQuery:
            def filter(self, *_args, **_kwargs):
                raise AssertionError('invalid threshold must not query products')

        monkeypatch.setattr(Product, 'query', ForbiddenQuery())

    def test_low_stock_default_threshold(self, client):
        """Test endpoint con umbral por defecto (10)"""
        # Crear productos con stocks variados
        products_data = [
            {'name': 'P1', 'price': 10.0, 'cost': 5.0, 'stock': 5, 'category_id': self.cat_id, 'sku': 'P1-SKU'},
            {'name': 'P2', 'price': 20.0, 'cost': 8.0, 'stock': 10, 'category_id': self.cat_id, 'sku': 'P2-SKU'},
            {'name': 'P3', 'price': 30.0, 'cost': 12.0, 'stock': 15, 'category_id': self.cat_id, 'sku': 'P3-SKU'},
            {'name': 'P4', 'price': 40.0, 'cost': 20.0, 'stock': 2, 'category_id': self.cat_id, 'sku': 'P4-SKU'},
        ]
        self._create_products(products_data)

        response = client.get('/api/products/low-stock')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 3  # P1, P2, P4
        items = data['data']
        # Orden ascendente por stock
        assert items[0]['stock'] == 2
        assert items[1]['stock'] == 5
        assert items[2]['stock'] == 10
        # Verificar campos y restock_value
        assert all(k in items[0] for k in ('id', 'name', 'sku', 'stock', 'restock_value'))
        # P1: restock_value = 5 * (10 - 5) = 25
        assert items[1]['restock_value'] == 25.0
        # P2: restock_value = 8 * (10 - 10) = 0
        assert items[2]['restock_value'] == 0.0
        # P4: restock_value = 20 * (10 - 2) = 160
        assert items[0]['restock_value'] == 160.0

    def test_low_stock_custom_threshold(self, client):
        """Test endpoint con umbral personalizado"""
        products_data = [
            {'name': 'A', 'price': 10.0, 'cost': 3.0, 'stock': 3, 'category_id': self.cat_id, 'sku': 'A-SKU'},
            {'name': 'B', 'price': 20.0, 'cost': 5.0, 'stock': 8, 'category_id': self.cat_id, 'sku': 'B-SKU'},
            {'name': 'C', 'price': 30.0, 'cost': 7.0, 'stock': 12, 'category_id': self.cat_id, 'sku': 'C-SKU'},
        ]
        self._create_products(products_data)

        response = client.get('/api/products/low-stock?threshold=8')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 2  # A (3), B (8)
        items = data['data']
        assert items[0]['stock'] == 3
        assert items[1]['stock'] == 8
        # A: restock_value = 3 * (8 - 3) = 15
        assert items[0]['restock_value'] == 15.0
        # B is exactly at the inclusive threshold.
        assert items[1]['restock_value'] == 0.0

    def test_low_stock_negative_threshold(self, client, monkeypatch):
        """Test que umbral negativo responde 400 sin consultar la base"""
        self._forbid_product_query(monkeypatch)
        response = client.get('/api/products/low-stock?threshold=-5')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'negativo' in data['error'].lower()

    def test_low_stock_non_integer_threshold(self, client, monkeypatch):
        """Test que umbral no entero responde 400 sin consultar la base"""
        self._forbid_product_query(monkeypatch)
        response = client.get('/api/products/low-stock?threshold=abc')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'entero' in data['error'].lower()

    def test_low_stock_empty_result(self, client):
        """Test que no hay resultados responde 200 con lista vacía"""
        # Crear productos con stock alto
        products_data = [
            {'name': 'High1', 'price': 10.0, 'cost': 5.0, 'stock': 20, 'category_id': self.cat_id, 'sku': 'H1-SKU'},
            {'name': 'High2', 'price': 20.0, 'cost': 8.0, 'stock': 30, 'category_id': self.cat_id, 'sku': 'H2-SKU'},
        ]
        self._create_products(products_data)

        response = client.get('/api/products/low-stock?threshold=5')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 0
        assert data['data'] == []

    def test_low_stock_order_ascending(self, client):
        """Test que el orden es ascendente por stock"""
        products_data = [
            {'name': 'Z', 'price': 10.0, 'cost': 1.0, 'stock': 100, 'category_id': self.cat_id, 'sku': 'Z-SKU'},
            {'name': 'Y', 'price': 10.0, 'cost': 1.0, 'stock': 50, 'category_id': self.cat_id, 'sku': 'Y-SKU'},
            {'name': 'X', 'price': 10.0, 'cost': 1.0, 'stock': 10, 'category_id': self.cat_id, 'sku': 'X-SKU'},
            {'name': 'W', 'price': 10.0, 'cost': 1.0, 'stock': 5, 'category_id': self.cat_id, 'sku': 'W-SKU'},
        ]
        self._create_products(products_data)

        response = client.get('/api/products/low-stock?threshold=100')
        assert response.status_code == 200
        data = json.loads(response.data)
        items = data['data']
        stocks = [it['stock'] for it in items]
        assert stocks == sorted(stocks)  # ascending
