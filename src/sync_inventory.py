import os
import json
from typing import Dict, List
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class InventorySync:
    def __init__(self, tiendanube_credentials: Dict):
        # Credenciales de Tiendanube
        self.tiendanube_base_url = tiendanube_credentials['base_url']
        self.tiendanube_headers = tiendanube_credentials['headers']
        
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

    def get_shopify_inventory_level(self, inventory_item_id: str, location_id: str) -> int:
        """Obtiene el nivel de inventario actual de un producto en Shopify"""
        url = f'{self.shopify_store_url}/admin/api/2024-01/inventory_levels.json'
        params = {
            'inventory_item_ids': inventory_item_id,
            'location_ids': location_id
        }
        response = requests.get(url, headers=self.shopify_headers, params=params)
        if response.status_code == 200:
            levels = response.json().get('inventory_levels', [])
            if levels:
                return levels[0].get('available', 0)
        return 0

    def set_shopify_inventory(self, inventory_item_id: str, location_id: str, new_quantity: int, current_quantity: int):
        """Establece el inventario de un producto en Shopify a un valor específico"""
        # Solo actualizar si hay diferencia en el stock
        if current_quantity == new_quantity:
            print(f"ℹ️ El stock ya está actualizado ({current_quantity}), no se requieren cambios")
            return True

        url = f'{self.shopify_store_url}/admin/api/2024-01/inventory_levels/set.json'
        data = {
            'inventory_item_id': inventory_item_id,
            'location_id': location_id,
            'available': new_quantity
        }
        print(f"\n🔄 Actualizando inventario en Shopify:")
        print(f"Stock actual: {current_quantity}")
        print(f"Nuevo stock: {new_quantity}")
        print(f"Datos: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=self.shopify_headers, json=data)
        if response.status_code != 200:
            print(f"❌ Error al actualizar inventario en Shopify:")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            raise Exception(f'Error al actualizar inventario en Shopify: {response.text}')
        print("✅ Inventario actualizado correctamente en Shopify")
        return True

    def get_shopify_locations(self) -> List[Dict]:
        """Obtiene todas las ubicaciones de Shopify"""
        url = f'{self.shopify_store_url}/admin/api/2024-01/locations.json'
        print(f"\n🔄 Obteniendo ubicaciones de Shopify desde: {url}")
        response = requests.get(url, headers=self.shopify_headers)
        if response.status_code == 200:
            locations = response.json()['locations']
            print(f"✅ Se encontraron {len(locations)} ubicaciones en Shopify")
            # Mostrar todas las ubicaciones disponibles
            for loc in locations:
                print(f"   - {loc['name']} (ID: {loc['id']})")
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
            
            # Buscar específicamente la ubicación "Shop location"
            shop_location = next((loc for loc in locations if loc['name'] == 'Shop location'), None)
            if not shop_location:
                raise Exception("No se encontró la ubicación 'Shop location' en Shopify")
            
            shop_location_id = shop_location['id']
            print(f"✅ Usando ubicación en Shopify: Shop location (ID: {shop_location_id})")

            # Crear mapeo de SKUs de Shopify para facilitar la búsqueda
            shopify_sku_map = {}
            for product in shopify_products:
                for variant in product.get('variants', []):
                    if variant.get('sku'):
                        shopify_sku_map[variant['sku']] = {
                            'inventory_item_id': variant['inventory_item_id'],
                            'product_id': product['id'],
                            'variant_id': variant['id'],
                            'current_stock': self.get_shopify_inventory_level(variant['inventory_item_id'], shop_location_id)
                        }
            
            print(f"✅ Se encontraron {len(shopify_sku_map)} productos con SKU en Shopify")
            print("SKUs disponibles en Shopify:", list(shopify_sku_map.keys()))

            # Actualizar inventario de Shopify basado en Tiendanube
            productos_actualizados = 0
            productos_no_encontrados = 0
            productos_sin_cambios = 0

            for product in tiendanube_products:
                product_id = str(product.get('id'))
                
                if product.get('variants'):
                    for variant in product.get('variants', []):
                        variant_id = str(variant.get('id'))
                        # Usar el formato producto-variante para el SKU
                        sku = f"{product_id}-{variant_id}"
                        
                        print(f"\n📦 Procesando producto ID: {product_id}, variante ID: {variant_id}")
                        print(f"Buscando SKU en Shopify: {sku}")
                        
                        if sku in shopify_sku_map:
                            shopify_data = shopify_sku_map[sku]
                            print(f"✅ SKU encontrado en Shopify")
                            print(f"Stock en Tiendanube: {variant['stock']}")
                            
                            # Actualizar stock solo si hay diferencia
                            if self.set_shopify_inventory(
                                shopify_data['inventory_item_id'],
                                shop_location_id,
                                variant['stock'],
                                shopify_data['current_stock']
                            ):
                                productos_actualizados += 1
                            else:
                                productos_sin_cambios += 1
                        else:
                            print(f"⚠️ SKU no encontrado en Shopify: {sku}")
                            productos_no_encontrados += 1
                else:
                    # Para productos sin variantes, usar solo el ID del producto
                    sku = product_id
                    print(f"\n📦 Procesando producto simple ID: {product_id}")
                    print(f"Buscando SKU en Shopify: {sku}")
                    
                    if sku in shopify_sku_map:
                        shopify_data = shopify_sku_map[sku]
                        print(f"✅ SKU encontrado en Shopify")
                        print(f"Stock en Tiendanube: {product.get('stock', 0)}")
                        
                        # Actualizar stock solo si hay diferencia
                        if self.set_shopify_inventory(
                            shopify_data['inventory_item_id'],
                            shop_location_id,
                            product.get('stock', 0),
                            shopify_data['current_stock']
                        ):
                            productos_actualizados += 1
                        else:
                            productos_sin_cambios += 1
                    else:
                        print(f"⚠️ SKU no encontrado en Shopify: {sku}")
                        productos_no_encontrados += 1

            print("\n✅ Sincronización completada")
            print(f"📊 Resumen:")
            print(f"- Productos actualizados: {productos_actualizados}")
            print(f"- Productos sin cambios: {productos_sin_cambios}")
            print(f"- Productos no encontrados: {productos_no_encontrados}")

        except Exception as e:
            print(f"\n❌ Error durante la sincronización: {str(e)}")

def main():
    # Obtener todas las credenciales de Tiendanube
    tiendanube_credentials = json.loads(os.getenv('TIENDANUBE_CREDENTIALS', '[]').strip("'"))
    if not tiendanube_credentials:
        raise Exception("No se encontraron credenciales de Tiendanube")
    
    print(f"🔄 Procesando {len(tiendanube_credentials)} tiendas...")
    
    # Estadísticas globales
    total_productos_actualizados = 0
    total_productos_sin_cambios = 0
    total_productos_no_encontrados = 0
    
    # Procesar cada tienda
    for i, credentials in enumerate(tiendanube_credentials, 1):
        try:
            print(f"\n📦 Procesando tienda {i}/{len(tiendanube_credentials)}")
            print(f"🔹 URL: {credentials['base_url']}")
            
            # Inicializar sincronizador con las credenciales actuales
            sync = InventorySync(credentials)
            
            # Realizar la sincronización
            sync.sync_inventory()
            
        except Exception as e:
            print(f"❌ Error durante la sincronización de la tienda {i}: {e}")
            continue
    
    print(f"\n🎉 Proceso completado!")

if __name__ == "__main__":
    main()