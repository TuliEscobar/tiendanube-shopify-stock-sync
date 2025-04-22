import os
import json
import time
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv
<<<<<<< HEAD
from src.store_config import StoreConfig
from src.shopify import ShopifyAPI
from src.tiendanube import TiendanubeAPI
from src.stock_tracker import StockTracker
from src.stock_database import StockDatabase
=======
from stock_cache_manager import StockCacheManager
import logging
>>>>>>> 5e26fc79081e2488caab237c9e7a924862fd82ba

# Cargar variables de entorno
load_dotenv()

<<<<<<< HEAD
# Inicializar el tracker de stock si estamos en modo validación
VALIDATE_STOCK = os.environ.get('STOCK_VALIDATION') == '1'
stock_tracker = StockTracker() if VALIDATE_STOCK else None

# Inicializar la base de datos de stock
stock_db = StockDatabase()
=======
logger = logging.getLogger(__name__)
>>>>>>> 5e26fc79081e2488caab237c9e7a924862fd82ba

class InventorySync:
    def __init__(self, store_config: Dict):
        """
        Inicializa el sincronizador de inventario
        
        Args:
            store_config (Dict): Configuración de la tienda desde el Excel
        """
        # Inicializar APIs
        self.tiendanube = TiendanubeAPI(store_config=store_config)
        self.shopify = ShopifyAPI()
        
        # Control de rate limits
        self.last_request_time = time.time()
        self.min_request_interval = 0.5  # 500ms entre llamadas
        
        # Contadores
        self.productos_actualizados = 0
        self.productos_sin_cambios = 0
        self.productos_no_encontrados = 0
        self.variantes_creadas = 0
        
        # Inicializar el gestor de caché
        store_id = tiendanube_credentials['base_url'].split('/')[-1]
        self.cache_manager = StockCacheManager(f"stock_cache_{store_id}.json")
        
        print("✅ Inicialización completada")
        print(f"🔹 URL Tiendanube: {store_config['api_url']}")
        print(f"🔹 URL Shopify: {self.shopify.api_url}")

    def _wait_for_rate_limit(self):
        """Espera el tiempo necesario para respetar el rate limit"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _make_shopify_request(self, method, endpoint, **kwargs):
        """Realiza una petición a Shopify respetando los rate limits"""
        self._wait_for_rate_limit()
        
        # Usar la URL base de la API sin el endpoint
        url = f'{self.shopify.api_url}/{endpoint}'
        response = requests.request(
            method=method,
            url=url,
            headers=self.shopify.headers,
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
        print("\n🔄 Obteniendo productos de Tiendanube")
        try:
            products = self.tiendanube.get_products()
            print(f"✅ Se encontraron {len(products)} productos en Tiendanube")
            return products
        except Exception as e:
            print(f"❌ Error al obtener productos de Tiendanube: {str(e)}")
            raise

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

<<<<<<< HEAD
    def find_shopify_product_by_tiendanube_id(self, tiendanube_id: str) -> Optional[Dict]:
        """Busca un producto en Shopify por el ID de Tiendanube usando SKU"""
        try:
            response = self._make_shopify_request(
                'GET',
                'products.json',
                params={'limit': 250}
            )
            
            if response.status_code != 200:
                raise Exception(f'Error al buscar producto: {response.text}')
            
            products = response.json()['products']
            for product in products:
                # Buscar en las variantes si alguna tiene el SKU base del producto
                for variant in product.get('variants', []):
                    if variant.get('sku', '').startswith(str(tiendanube_id)):
                        return product
            
            return None
            
        except Exception as e:
            print(f"❌ Error al buscar producto en Shopify: {str(e)}")
            return None

    def create_shopify_variant(self, shopify_product: Dict, tiendanube_product: Dict, tiendanube_variant: Dict) -> Dict:
        """Crea una nueva variante en un producto existente de Shopify"""
        try:
            # Preparar las opciones basadas en las existentes en el producto
            variant_data = {
                'variant': {
                    'product_id': shopify_product['id'],
                    'sku': f"{tiendanube_product['id']}-{tiendanube_variant['id']}",
                    'price': str(tiendanube_variant.get('price', '0.00')),
                    'inventory_management': 'shopify',
                    'inventory_policy': 'deny'
                }
            }

            # Agregar los valores de las opciones existentes
            for i, option in enumerate(shopify_product.get('options', []), 1):
                option_name = option['name'].lower()
                option_values = tiendanube_variant.get('values', [])
                
                # Buscar el valor correspondiente en las opciones de Tiendanube
                option_value = None
                for value in option_values:
                    if value.get('es'):
                        option_value = value['es']
                        break
                
                if option_value:
                    variant_data['variant'][f'option{i}'] = option_value
                else:
                    # Si no hay valor, usar el primer valor disponible de la opción
                    variant_data['variant'][f'option{i}'] = option['values'][0]

            print(f"🔄 Creando variante con datos: {json.dumps(variant_data, indent=2)}")

            # Crear la variante
            response = self._make_shopify_request(
                'POST',
                f'products/{shopify_product["id"]}/variants.json',
                json=variant_data
            )

            if response.status_code != 201:
                print(f"❌ Error al crear variante. Respuesta: {response.text}")
                raise Exception(f'Error al crear variante: {response.text}')

            new_variant = response.json()['variant']
            print(f"✅ Nueva variante creada en Shopify - SKU: {variant_data['variant']['sku']}")
            
            # Establecer el inventario inicial
            self.set_shopify_inventory(
                new_variant['inventory_item_id'],
                self.shop_location_id,
                tiendanube_variant['stock'],
                0,
                {
                    'product_id': shopify_product['id'],
                    'variant_id': new_variant['id']
                }
            )
            
            return new_variant
            
        except Exception as e:
            print(f"❌ Error al crear variante en Shopify: {str(e)}")
            raise

    def sync_inventory(self):
        """Sincroniza el inventario desde Tiendanube hacia Shopify"""
=======
    def create_variant(self, product_id: str, variant_data: Dict) -> Dict:
        """Crea una nueva variante para un producto existente en Shopify"""
>>>>>>> 5e26fc79081e2488caab237c9e7a924862fd82ba
        try:
            response = self._make_shopify_request(
                'POST',
                f'products/{product_id}/variants.json',
                json={'variant': variant_data}
            )
            
<<<<<<< HEAD
            # Reiniciar contadores
            self.productos_actualizados = 0
            self.productos_sin_cambios = 0
            self.productos_no_encontrados = 0
            self.variantes_creadas = 0
            
            # 1. Obtener productos de Tiendanube
            tiendanube_products = self.get_tiendanube_products()
            
            # 2. Obtener productos de Shopify
            shopify_products = self.get_shopify_products()
            
            # 3. Obtener ubicación principal de Shopify
            locations = self.get_shopify_locations()
            shop_location = next((loc for loc in locations if loc['name'] == 'Shop location'), None)
            if not shop_location:
                raise Exception("No se encontró la ubicación 'Shop location'")
            
            self.shop_location_id = shop_location['id']
            
            # 4. Crear mapeo de SKUs de Shopify
            shopify_sku_map = {}
            for product in shopify_products:
                for variant in product.get('variants', []):
                    if variant.get('sku'):
                        shopify_sku_map[variant['sku']] = {
                            'inventory_item_id': variant['inventory_item_id'],
                            'product_id': product['id'],
                            'variant_id': variant['id']
                        }
            
            # 5. Procesar productos de Tiendanube
            for product in tiendanube_products:
                product_id = str(product.get('id'))
                
                if product.get('variants'):
                    # Producto con variantes
                    for variant in product.get('variants', []):
                        variant_id = str(variant.get('id'))
                        sku = f"{product_id}-{variant_id}"
                        
                        if sku in shopify_sku_map:
                            # Actualizar inventario de variante existente
                            shopify_data = shopify_sku_map[sku]
                            current_stock = self.get_shopify_inventory_level(
                                shopify_data['inventory_item_id'],
                                self.shop_location_id
                            )
                            
                            if self.set_shopify_inventory(
                                shopify_data['inventory_item_id'],
                                self.shop_location_id,
                                variant['stock'],
                                current_stock,
                                shopify_data
                            ):
                                self.productos_actualizados += 1
                            else:
                                self.productos_sin_cambios += 1
                        else:
                            # Intentar crear la variante
                            print(f"🔄 Variante no encontrada, intentando crearla - SKU: {sku}")
                            shopify_product = self.find_shopify_product_by_tiendanube_id(product_id)
                            
                            if shopify_product:
                                try:
                                    # Obtener el producto completo de Shopify
                                    response = self._make_shopify_request(
                                        'GET',
                                        f'products/{shopify_product["id"]}.json'
                                    )
                                    if response.status_code != 200:
                                        raise Exception(f'Error al obtener producto: {response.text}')
                                    
                                    shopify_product_full = response.json()['product']
                                    new_variant = self.create_shopify_variant(
                                        shopify_product_full,
                                        product,
                                        variant
                                    )
                                    
                                    # Actualizar el mapeo de SKUs con la nueva variante
                                    shopify_sku_map[new_variant['sku']] = {
                                        'inventory_item_id': new_variant['inventory_item_id'],
                                        'product_id': shopify_product['id'],
                                        'variant_id': new_variant['id']
                                    }
                                    
                                    self.variantes_creadas += 1
                                    
                                except Exception as e:
                                    print(f"❌ No se pudo crear la variante: {str(e)}")
                                    self.productos_no_encontrados += 1
                            else:
                                print(f"❌ Producto base no encontrado en Shopify - SKU: {sku}")
                                self.productos_no_encontrados += 1
                else:
                    # Producto simple
                    sku = product_id
                    if sku in shopify_sku_map:
                        shopify_data = shopify_sku_map[sku]
                        current_stock = self.get_shopify_inventory_level(
                            shopify_data['inventory_item_id'],
                            self.shop_location_id
                        )
                        
                        if self.set_shopify_inventory(
                            shopify_data['inventory_item_id'],
                            self.shop_location_id,
                            product.get('stock', 0),
                            current_stock,
                            shopify_data
                        ):
                            self.productos_actualizados += 1
                        else:
                            self.productos_sin_cambios += 1
                    else:
                        print(f"❌ Producto no encontrado en Shopify - SKU: {sku} (Tiendanube ID: {product_id})")
                        self.productos_no_encontrados += 1

            print("\n✅ Sincronización completada")
            print(f"📊 Resumen de la tienda:")
            print(f"- Productos actualizados: {self.productos_actualizados}")
            print(f"- Productos sin cambios: {self.productos_sin_cambios}")
            print(f"- Productos no encontrados: {self.productos_no_encontrados}")
            print(f"- Variantes nuevas creadas: {self.variantes_creadas}")

=======
            if response.status_code != 201:
                raise Exception(f'Error al crear variante: {response.text}')
                
            return response.json()['variant']
            
>>>>>>> 5e26fc79081e2488caab237c9e7a924862fd82ba
        except Exception as e:
            print(f"❌ Error al crear variante: {str(e)}")
            raise

<<<<<<< HEAD
def should_update_stock(store_id: str, product_id: str, new_stock: int) -> bool:
    """
    Determina si se debe actualizar el stock basado en el último valor conocido
    
    Args:
        store_id (str): ID de la tienda
        product_id (str): ID del producto
        new_stock (int): Nuevo valor de stock
        
    Returns:
        bool: True si el stock debe actualizarse, False si no
    """
    if not VALIDATE_STOCK or stock_tracker is None:
        return True
        
    last_stock = stock_tracker.get_last_stock(store_id, product_id)
    
    # Si no hay stock anterior registrado, actualizar
    if last_stock is None:
        stock_tracker.update_stock(store_id, product_id, new_stock)
        return True
    
    # Si el stock es diferente, actualizar
    if last_stock != new_stock:
        stock_tracker.update_stock(store_id, product_id, new_stock)
        return True
    
    return False

def sync_inventory(store_config: Dict):
    """Sincroniza el inventario de una tienda"""
    try:
        print("\n🔄 Configuración de la tienda:")
        print(f"   API URL: {store_config.get('api_url')}")
        print(f"   Token: {store_config.get('token', '')[:20]}...")
        
        # Inicializar APIs
        tiendanube = TiendanubeAPI(store_config=store_config)
        shopify = ShopifyAPI()
        
        # Obtener productos de Tiendanube
        print("\n🔄 Obteniendo productos de Tiendanube...")
        products = tiendanube.get_products()
        
        if not products:
            print("❌ No se encontraron productos en Tiendanube")
            return
            
        print(f"✅ Se encontraron {len(products)} productos")
        
        # Contadores
        updates = 0
        no_changes = 0
        errors = 0
        
        # Usar store_id de la URL de la API
        store_id = store_config['api_url'].split('/')[-1]
        
        # Procesar cada producto
        for product in products:
            try:
                tiendanube_id = str(product['id'])
                print(f"\n🔍 Procesando producto ID: {tiendanube_id}")
                
                # Obtener stock actual
                current_stock = sum(variant.get('stock', 0) for variant in product.get('variants', []))
                if not product.get('variants'):
                    current_stock = product.get('stock', 0)
                
                print(f"📊 Stock actual en Tiendanube: {current_stock}")
                
                # Obtener último registro de stock
                last_record = stock_db.get_last_stock(store_id, tiendanube_id)
                if last_record:
                    print(f"📊 Último stock registrado: {last_record.get('current_tiendanube_stock', 0)}")
                else:
                    print("📊 No hay registro previo de stock")
                
                # Forzar sincronización para depuración
                print(f"🔄 Intentando sincronizar con Shopify...")
                if shopify.sync_products_from_tiendanube(product):
                    updates += 1
                    print(f"✅ Sincronización exitosa")
                    # Actualizar registro en la base de datos
                    stock_db.update_stock(
                        store_id,
                        tiendanube_id,
                        current_stock,
                        current_stock
                    )
                else:
                    print(f"❌ Error en la sincronización")
                    errors += 1
                    
            except Exception as e:
                print(f"❌ Error procesando producto {tiendanube_id}: {str(e)}")
                errors += 1
                continue
                
        # Resumen
        print(f"\n📊 Sincronización completada:")
        print(f"- Actualizados: {updates}")
        print(f"- Sin cambios: {no_changes}")
        print(f"- Errores: {errors}")
        
    except Exception as e:
        print(f"❌ Error general en la sincronización: {str(e)}")
        raise
=======
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
>>>>>>> 5e26fc79081e2488caab237c9e7a924862fd82ba

def main():
    try:
        store_config = StoreConfig()
        stores = store_config.get_all_stores()
        
        if not stores:
            print("No se encontraron tiendas configuradas")
            return
        
        print(f"Iniciando sincronización para {len(stores)} tiendas")
        
        for i, store in enumerate(stores, 1):
            try:
                print(f"\nProcesando tienda {store.get('category')} ({i}/{len(stores)})")
                sync_inventory(store)
                
                if i < len(stores):
                    time.sleep(5)
                
            except Exception as e:
                print(f"Error en tienda {i}: {str(e)}")
                continue
        
        print("\nProceso completado")
        
    except Exception as e:
        print(f"❌ Error en el proceso principal: {str(e)}")
        raise

if __name__ == "__main__":
    main()