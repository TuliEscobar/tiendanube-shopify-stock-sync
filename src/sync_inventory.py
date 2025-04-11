import os
import json
from typing import Dict, List
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class InventorySync:
    def __init__(self):
        # Credenciales de Tiendanube
        tiendanube_credentials = json.loads(os.getenv('TIENDANUBE_CREDENTIALS', '[]').strip("'"))
        if not tiendanube_credentials:
            raise Exception("No se encontraron credenciales de Tiendanube")
        
        self.tiendanube_credentials = tiendanube_credentials[0]  # Usar la primera configuración
        self.tiendanube_base_url = self.tiendanube_credentials['base_url']
        self.tiendanube_headers = self.tiendanube_credentials['headers']
        
        # Credenciales de Shopify
        self.shopify_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        shopify_shop_url = os.getenv('SHOPIFY_SHOP_URL')
        
        if not all([self.shopify_token, shopify_shop_url]):
            raise Exception("Faltan credenciales de Shopify")
        
        # Formatear la URL de Shopify
        self.shopify_store_url = f'https://{shopify_shop_url}'
        
        self.shopify_headers = {
            'X-Shopify-Access-Token': self.shopify_token,
            'Content-Type': 'application/json'
        }
        print("✅ Inicialización completada")
        print(f"🔹 URL Tiendanube: {self.tiendanube_base_url}")
        print(f"🔹 URL Shopify: {self.shopify_store_url}")

    def get_tiendanube_products(self) -> List[Dict]:
        """Obtiene todos los productos de Tiendanube"""
        url = f'{self.tiendanube_base_url}/products'
        print(f"\n🔄 Obteniendo productos de Tiendanube desde: {url}")
        response = requests.get(url, headers=self.tiendanube_headers)
        if response.status_code == 200:
            products = response.json()
            print(f"✅ Se encontraron {len(products)} productos en Tiendanube")
            return products
        else:
            print(f"❌ Error al obtener productos de Tiendanube:")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            raise Exception(f'Error al obtener productos de Tiendanube: {response.text}')

    def get_shopify_products(self) -> List[Dict]:
        """Obtiene todos los productos de Shopify"""
        url = f'{self.shopify_store_url}/admin/api/2024-01/products.json'
        print(f"\n🔄 Obteniendo productos de Shopify desde: {url}")
        response = requests.get(url, headers=self.shopify_headers)
        if response.status_code == 200:
            products = response.json()['products']
            print(f"✅ Se encontraron {len(products)} productos en Shopify")
            return products
        else:
            print(f"❌ Error al obtener productos de Shopify:")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            raise Exception(f'Error al obtener productos de Shopify: {response.text}')

    def update_tiendanube_inventory(self, product_id: str, variant_id: str, quantity: int):
        """Actualiza el inventario de un producto en Tiendanube"""
        url = f'{self.tiendanube_base_url}/products/{product_id}/variants/{variant_id}'
        data = {'stock': quantity}
        response = requests.put(url, headers=self.tiendanube_headers, json=data)
        if response.status_code != 200:
            raise Exception(f'Error al actualizar inventario en Tiendanube: {response.text}')

    def update_shopify_inventory(self, inventory_item_id: str, location_id: str, quantity: int):
        """Actualiza el inventario de un producto en Shopify"""
        url = f'{self.shopify_store_url}/admin/api/2024-01/inventory_levels/set.json'
        data = {
            'inventory_item_id': inventory_item_id,
            'location_id': location_id,
            'available': quantity
        }
        print(f"\n🔄 Actualizando inventario en Shopify:")
        print(f"URL: {url}")
        print(f"Datos: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=self.shopify_headers, json=data)
        if response.status_code != 200:
            print(f"❌ Error al actualizar inventario en Shopify:")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            raise Exception(f'Error al actualizar inventario en Shopify: {response.text}')
        print("✅ Inventario actualizado correctamente en Shopify")

    def get_shopify_locations(self) -> List[Dict]:
        """Obtiene todas las ubicaciones de Shopify"""
        url = f'{self.shopify_store_url}/admin/api/2024-01/locations.json'
        print(f"\n🔄 Obteniendo ubicaciones de Shopify desde: {url}")
        response = requests.get(url, headers=self.shopify_headers)
        if response.status_code == 200:
            locations = response.json()['locations']
            print(f"✅ Se encontraron {len(locations)} ubicaciones en Shopify")
            return locations
        else:
            print(f"❌ Error al obtener ubicaciones de Shopify:")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            raise Exception(f'Error al obtener ubicaciones de Shopify: {response.text}')

    def sync_inventory(self):
        """Sincroniza el inventario desde Tiendanube hacia Shopify"""
        try:
            print("\n🔄 Iniciando sincronización de inventario...")
            
            # Obtener productos de ambas plataformas
            tiendanube_products = self.get_tiendanube_products()
            shopify_products = self.get_shopify_products()
            
            # Obtener la ubicación principal de Shopify
            locations = self.get_shopify_locations()
            if not locations:
                raise Exception("No se encontraron ubicaciones en Shopify")
            main_location_id = locations[0]['id']
            print(f"✅ Usando ubicación principal de Shopify: {main_location_id}")

            # Crear mapeo de SKUs de Shopify para facilitar la búsqueda
            shopify_sku_map = {}
            for product in shopify_products:
                for variant in product.get('variants', []):
                    if variant.get('sku'):
                        shopify_sku_map[variant['sku']] = {
                            'inventory_item_id': variant['inventory_item_id']
                        }
            print(f"✅ Se encontraron {len(shopify_sku_map)} SKUs únicos en Shopify")

            # Actualizar inventario de Shopify basado en Tiendanube
            productos_actualizados = 0
            productos_no_encontrados = 0
            for product in tiendanube_products:
                for variant in product.get('variants', []):
                    sku = variant.get('sku')
                    if sku and sku in shopify_sku_map:
                        shopify_data = shopify_sku_map[sku]
                        print(f"\n📦 Procesando SKU: {sku}")
                        print(f"Stock en Tiendanube: {variant['stock']}")
                        # Actualizar Shopify con el stock de Tiendanube
                        self.update_shopify_inventory(
                            shopify_data['inventory_item_id'],
                            main_location_id,
                            variant['stock']
                        )
                        productos_actualizados += 1
                    else:
                        if sku:
                            print(f"⚠️ SKU no encontrado en Shopify: {sku}")
                            productos_no_encontrados += 1

            print("\n✅ Sincronización completada")
            print(f"📊 Resumen:")
            print(f"- Productos actualizados: {productos_actualizados}")
            print(f"- Productos no encontrados: {productos_no_encontrados}")

        except Exception as e:
            print(f"\n❌ Error durante la sincronización: {str(e)}")

if __name__ == '__main__':
    sync = InventorySync()
    sync.sync_inventory() 