import os
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

class ShopifyAPI:
    def __init__(self):
        """Inicializa la API de Shopify con las credenciales del .env"""
        load_dotenv()
        
        self.api_url = os.getenv('SHOPIFY_STORE_URL')
        if not self.api_url:
            raise ValueError("SHOPIFY_STORE_URL no está configurado en .env")
            
        self.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        if not self.access_token:
            raise ValueError("SHOPIFY_ACCESS_TOKEN no está configurado en .env")
            
        self.headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
        
        print("✅ API de Shopify inicializada")
        print(f"🔹 URL: {self.api_url}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Realiza una petición a la API de Shopify
        
        Args:
            method (str): Método HTTP
            endpoint (str): Endpoint de la API
            **kwargs: Argumentos adicionales para la petición
            
        Returns:
            requests.Response: Respuesta de la API
        """
        url = f"{self.api_url}/admin/api/2023-01/{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        
        if response.status_code not in [200, 201]:
            print(f"❌ Error en petición a Shopify: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            raise Exception(f"Error en petición a Shopify: {response.status_code}")
            
        return response

    def get_locations(self) -> list:
        """
        Obtiene las ubicaciones de Shopify
        
        Returns:
            list: Lista de ubicaciones
        """
        response = self._make_request('GET', 'locations.json')
        return response.json()['locations']

    def find_variant_by_sku(self, sku: str) -> Optional[Dict]:
        """
        Busca una variante por SKU y retorna el producto y la variante
        
        Args:
            sku (str): SKU a buscar (ID de variante o producto en Tiendanube)
            
        Returns:
            Optional[Dict]: Tupla (producto, variante) o None si no se encuentra
        """
        response = self._make_request(
            'GET',
            'products.json',
            params={'limit': 250}
        )
        
        products = response.json()['products']
        for product in products:
            for variant in product.get('variants', []):
                if variant.get('sku') == sku:
                    return {'product': product, 'variant': variant}
        return None

    def update_variant_stock(self, inventory_item_id: str, location_id: str, new_quantity: int) -> bool:
        """
        Actualiza el stock de una variante
        
        Args:
            inventory_item_id (str): ID del item de inventario
            location_id (str): ID de la ubicación
            new_quantity (int): Nueva cantidad de stock
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            response = self._make_request(
                'POST',
                'inventory_levels/set.json',
                json={
                    'inventory_item_id': str(inventory_item_id),
                    'location_id': str(location_id),
                    'available': new_quantity
                }
            )
            return True
        except Exception as e:
            print(f"❌ Error al actualizar stock: {e}")
            return False

    def sync_products_from_tiendanube(self, product: Dict) -> bool:
        """
        Sincroniza el stock de un producto de Tiendanube a Shopify
        
        Args:
            product (Dict): Producto de Tiendanube
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            # Obtener ubicación principal
            locations = self.get_locations()
            shop_location = next((loc for loc in locations if loc['name'] == 'Shop location'), None)
            if not shop_location:
                raise Exception("No se encontró la ubicación 'Shop location'")
            
            # Verificar si el producto tiene variantes
            variants = product.get('variants', [])
            if not variants:
                # Producto sin variantes - usar ID de producto como SKU
                sku = str(product['id'])
                stock = product.get('stock', 0)
                if stock is None:  # Stock infinito
                    stock = 999
                    print(f"🔄 Convirtiendo stock infinito a 999 para producto {sku}")
                    
                # Buscar producto en Shopify por SKU
                print(f"🔍 Buscando producto en Shopify con SKU: {sku}")
                result = self.find_variant_by_sku(sku)
                if not result:
                    print(f"❌ No se encontró el producto con SKU (ID Tiendanube): {sku}")
                    return False
                
                # Obtener inventory_item_id
                inventory_item_id = result['variant'].get('inventory_item_id')
                if not inventory_item_id:
                    print(f"❌ No se encontró inventory_item_id para SKU: {sku}")
                    return False
                
                # Actualizar stock
                print(f"🔄 Actualizando stock para producto {sku} a {stock}")
                success = self.update_variant_stock(
                    inventory_item_id,
                    shop_location['id'],
                    stock
                )
                
                if success:
                    print(f"✅ Stock actualizado para producto {sku}: {stock}")
                return success
            
            # Producto con variantes - procesar cada variante
            success = True
            for variant in variants:
                # Usar ID de variante como SKU
                sku = str(variant['id'])
                stock = variant.get('stock', 0)
                if stock is None:  # Stock infinito
                    stock = 999
                    print(f"🔄 Convirtiendo stock infinito a 999 para variante {sku}")
                
                # Buscar variante en Shopify por SKU
                print(f"🔍 Buscando variante en Shopify con SKU: {sku}")
                result = self.find_variant_by_sku(sku)
                if not result:
                    print(f"❌ No se encontró la variante con SKU (ID Tiendanube): {sku}")
                    success = False
                    continue
                
                # Obtener inventory_item_id
                inventory_item_id = result['variant'].get('inventory_item_id')
                if not inventory_item_id:
                    print(f"❌ No se encontró inventory_item_id para SKU: {sku}")
                    success = False
                    continue
                
                # Actualizar stock
                print(f"🔄 Actualizando stock para variante {sku} a {stock}")
                if self.update_variant_stock(
                    inventory_item_id,
                    shop_location['id'],
                    stock
                ):
                    print(f"✅ Stock actualizado para variante {sku}: {stock}")
                else:
                    success = False
            
            return success
            
        except Exception as e:
            print(f"❌ Error sincronizando producto {product.get('id')}: {e}")
            return False 