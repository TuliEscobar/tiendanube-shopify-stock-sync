import os
import json
import time
from typing import Dict, List
import requests
from dotenv import load_dotenv
from stock_cache_manager import StockCacheManager
import logging

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

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
        
        # Control de rate limits
        self.last_request_time = time.time()
        self.min_request_interval = 0.5  # 500ms entre llamadas
        
        # Contadores
        self.productos_actualizados = 0
        self.productos_sin_cambios = 0
        self.productos_no_encontrados = 0
        
        # Inicializar el gestor de caché
        store_id = tiendanube_credentials['base_url'].split('/')[-1]
        self.cache_manager = StockCacheManager(f"stock_cache_{store_id}.json")
        
        print("✅ Inicialización completada")
        print(f"🔹 URL Tiendanube: {self.tiendanube_base_url}")
        print(f"🔹 URL Shopify: {self.shopify_store_url}")

    def _wait_for_rate_limit(self):
        """Espera el tiempo necesario para respetar el rate limit"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _make_shopify_request(self, method, endpoint, **kwargs):
        """Realiza una petición a Shopify respetando los rate limits"""
        self._wait_for_rate_limit()
        
        url = f'{self.shopify_store_url}/admin/api/2024-01/{endpoint}'
        response = requests.request(
            method=method,
            url=url,
            headers=self.shopify_headers,
            **kwargs
        )
        
        if response.status_code == 429:  # Rate limit exceeded
            retry_after = int(response.headers.get('Retry-After', 5))
            print(f"Rate limit excedido. Esperando {retry_after} segundos...")
            time.sleep(retry_after)
            return self._make_shopify_request(method, endpoint, **kwargs)
            
        return response

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
        print(f"\n🔄 Obteniendo productos de Shopify")
        products = []
        
        try:
            while True:
                response = self._make_shopify_request(
                    'GET',
                    'products.json',
                    params={'limit': 250, 'fields': 'id,variants'}
                )
                
                if response.status_code != 200:
                    raise Exception(f'Error al obtener productos: {response.text}')
                
                page_products = response.json()['products']
                products.extend(page_products)
                
                # Verificar si hay más páginas
                link_header = response.headers.get('Link', '')
                if 'rel="next"' not in link_header:
                    break
            
            print(f"✅ Se encontraron {len(products)} productos en Shopify")
            return products
            
        except Exception as e:
            print(f"❌ Error al obtener productos de Shopify: {str(e)}")
            raise

    def get_shopify_inventory_level(self, inventory_item_id: str, location_id: str) -> int:
        """Obtiene el nivel de inventario actual de un producto en Shopify"""
        try:
            response = self._make_shopify_request(
                'GET',
                'inventory_levels.json',
                params={
                    'inventory_item_ids': inventory_item_id,
                    'location_ids': location_id
                }
            )
            
            if response.status_code == 200:
                levels = response.json().get('inventory_levels', [])
                if levels:
                    return levels[0].get('available', 0)
            return 0
            
        except Exception as e:
            print(f"❌ Error al obtener nivel de inventario: {str(e)}")
            return 0

    def set_shopify_inventory(self, inventory_item_id: str, location_id: str, new_quantity: int, current_quantity: int, product_info: Dict):
        """Establece el inventario de un producto en Shopify"""
        if current_quantity == new_quantity:
            print(f"ℹ️ Stock sin cambios para producto ID: {product_info['product_id']}-{product_info['variant_id']} (Stock: {current_quantity})")
            self.productos_sin_cambios += 1
            return False

        try:
            response = self._make_shopify_request(
                'POST',
                'inventory_levels/set.json',
                json={
                    'inventory_item_id': inventory_item_id,
                    'location_id': location_id,
                    'available': new_quantity
                }
            )
            
            if response.status_code != 200:
                raise Exception(f'Error al actualizar inventario: {response.text}')
                
            print(f"✅ Stock actualizado - Producto ID: {product_info['product_id']}-{product_info['variant_id']} | {current_quantity} → {new_quantity}")
            return True
            
        except Exception as e:
            print(f"❌ Error al actualizar inventario para producto ID: {product_info['product_id']}-{product_info['variant_id']}: {str(e)}")
            return False

    def get_shopify_locations(self) -> List[Dict]:
        """Obtiene todas las ubicaciones de Shopify"""
        try:
            response = self._make_shopify_request('GET', 'locations.json')
            
            if response.status_code != 200:
                raise Exception(f'Error al obtener ubicaciones: {response.text}')
                
            locations = response.json()['locations']
            print(f"✅ Se encontraron {len(locations)} ubicaciones en Shopify")
            return locations
            
        except Exception as e:
            print(f"❌ Error al obtener ubicaciones: {str(e)}")
            raise

    def create_variant(self, product_id: str, variant_data: Dict) -> Dict:
        """Crea una nueva variante para un producto existente en Shopify"""
        try:
            response = self._make_shopify_request(
                'POST',
                f'products/{product_id}/variants.json',
                json={'variant': variant_data}
            )
            
            if response.status_code != 201:
                raise Exception(f'Error al crear variante: {response.text}')
                
            return response.json()['variant']
            
        except Exception as e:
            print(f"❌ Error al crear variante: {str(e)}")
            raise

    def set_tiendanube_stock(self, product_id: str, variant_id: str, new_quantity: int, current_quantity: int):
        """Establece el inventario de un producto en Tiendanube"""
        if current_quantity == new_quantity:
            print(f"ℹ️ Stock sin cambios en Tiendanube para producto ID: {product_id}-{variant_id} (Stock: {current_quantity})")
            return False

        try:
            # Para productos con variantes
            if variant_id != "0":
                url = f'{self.tiendanube_base_url}/products/{product_id}/variants/{variant_id}'
                data = {'stock': new_quantity}
            # Para productos simples
            else:
                url = f'{self.tiendanube_base_url}/products/{product_id}'
                data = {'stock': new_quantity}

            response = requests.put(url, headers=self.tiendanube_headers, json=data)
            
            if response.status_code != 200:
                raise Exception(f'Error al actualizar inventario: {response.text}')
                
            print(f"✅ Stock actualizado en Tiendanube - Producto ID: {product_id}-{variant_id} | {current_quantity} → {new_quantity}")
            return True
            
        except Exception as e:
            print(f"❌ Error al actualizar inventario en Tiendanube para producto ID: {product_id}-{variant_id}: {str(e)}")
            return False

    def sync_inventory(self):
        """
        Sincroniza el inventario entre Tiendanube y Shopify usando el caché de stock
        """
        logger.info("Iniciando sincronización de inventario")
        
        # Obtenemos productos de ambas plataformas
        tiendanube_products = self.get_tiendanube_products()
        logger.info(f"Productos encontrados en Tiendanube: {len(tiendanube_products)}")
        
        shopify_products = self.get_shopify_products()
        logger.info(f"Productos encontrados en Shopify: {len(shopify_products)}")
        
        # Obtenemos la ubicación principal de Shopify
        locations = self.get_shopify_locations()
        shop_location = next((loc for loc in locations if loc['name'] == 'Shop location'), None)
        if not shop_location:
            raise Exception("No se encontró la ubicación 'Shop location'")
        
        logger.info(f"Ubicación de Shopify encontrada: {shop_location['name']} ({shop_location['id']})")
        
        # Mapeamos productos por SKU para fácil acceso
        shopify_by_sku = {}
        total_variants = 0
        for product in shopify_products:
            for variant in product.get('variants', []):
                if variant.get('sku'):
                    total_variants += 1
                    shopify_by_sku[variant['sku']] = {
                        'inventory_item_id': variant['inventory_item_id'],
                        'location_id': shop_location['id'],
                        'product_id': product['id'],
                        'variant_id': variant['id']
                    }
        
        logger.info(f"Total de variantes en Shopify: {total_variants}")
        logger.info(f"SKUs mapeados: {len(shopify_by_sku)}")
        
        for tn_product in tiendanube_products:
            product_id = str(tn_product['id'])
            logger.info(f"\nProcesando producto Tiendanube ID: {product_id}")
            
            # Procesamos cada variante
            variants = tn_product.get('variants', [])
            logger.info(f"Variantes encontradas: {len(variants)}")
            
            for variant in variants:
                variant_id = str(variant['id'])
                sku = f"{product_id}-{variant_id}"
                current_stock = variant.get('stock', 0)
                
                logger.info(f"Procesando variante: {sku} (Stock actual: {current_stock})")
                
                # Si no existe en Shopify, continuamos
                if sku not in shopify_by_sku:
                    logger.warning(f"SKU {sku} no encontrado en Shopify")
                    continue
                    
                shopify_variant = shopify_by_sku[sku]
                shopify_stock = self.get_shopify_inventory_level(
                    shopify_variant['inventory_item_id'],
                    shopify_variant['location_id']
                )
                
                logger.info(f"Stock en Shopify: {shopify_stock}")
                
                # Verificamos si debemos actualizar Shopify
                shopify_updated = False
                if self.cache_manager.should_update_shopify(product_id, variant_id, current_stock, shopify_stock):
                    logger.info(f"Actualizando stock en Shopify para SKU {sku}: {current_stock}")
                    if self.set_shopify_inventory(
                        shopify_variant['inventory_item_id'],
                        shopify_variant['location_id'],
                        current_stock,
                        shopify_stock,
                        shopify_variant
                    ):
                        self.productos_actualizados += 1
                        self.cache_manager.update_stock(product_id, variant_id, current_stock, current_stock)
                        logger.info("✅ Stock actualizado en Shopify")
                        shopify_updated = True
                else:
                    self.productos_sin_cambios += 1
                    logger.info("ℹ️ No es necesario actualizar Shopify")
                
                # Solo verificamos Shopify si no se actualizó previamente
                if not shopify_updated:
                    # Verificamos si debemos actualizar Tiendanube (cuando Shopify tiene menos stock)
                    if self.cache_manager.should_update_tiendanube(product_id, variant_id, current_stock, shopify_stock):
                        logger.info(f"Actualizando stock en Tiendanube para SKU {sku}: {shopify_stock}")
                        if self.set_tiendanube_stock(product_id, variant_id, shopify_stock, current_stock):
                            self.cache_manager.update_stock(product_id, variant_id, shopify_stock, shopify_stock)
                            logger.info("✅ Stock actualizado en Tiendanube")
                    
        logger.info("\n=== Resumen de sincronización ===")
        logger.info(f"Productos actualizados: {self.productos_actualizados}")
        logger.info(f"Productos sin cambios: {self.productos_sin_cambios}")
        logger.info(f"Productos no encontrados: {self.productos_no_encontrados}")
        logger.info("Sincronización de inventario completada")

def main():
    try:
        # Obtener credenciales de Tiendanube
        tiendanube_credentials = json.loads(os.getenv('TIENDANUBE_CREDENTIALS', '[]').strip("'"))
        if not tiendanube_credentials:
            raise Exception("No se encontraron credenciales de Tiendanube")
        
        print(f"🔄 Procesando {len(tiendanube_credentials)} tiendas...")
        
        # Estadísticas globales
        total_actualizados = 0
        total_sin_cambios = 0
        total_no_encontrados = 0
        
        # Procesar cada tienda
        for i, credentials in enumerate(tiendanube_credentials, 1):
            try:
                print(f"\n📦 Procesando tienda {i}/{len(tiendanube_credentials)}")
                print(f"🔹 URL: {credentials['base_url']}")
                
                sync = InventorySync(credentials)
                sync.sync_inventory()
                
                # Acumular estadísticas
                total_actualizados += sync.productos_actualizados
                total_sin_cambios += sync.productos_sin_cambios
                total_no_encontrados += sync.productos_no_encontrados
                
                # Esperar entre tiendas para respetar rate limits
                if i < len(tiendanube_credentials):
                    print("\nEsperando 5 segundos antes de procesar la siguiente tienda...")
                    time.sleep(5)
                
            except Exception as e:
                print(f"❌ Error en tienda {i}: {str(e)}")
                continue
        
        # Mostrar resumen global
        print("\n🎉 Proceso completado para todas las tiendas!")
        print(f"📊 Resumen Global:")
        print(f"- Total productos actualizados: {total_actualizados}")
        print(f"- Total productos sin cambios: {total_sin_cambios}")
        print(f"- Total productos no encontrados: {total_no_encontrados}")
        
    except Exception as e:
        print(f"❌ Error global: {str(e)}")

if __name__ == "__main__":
    main()