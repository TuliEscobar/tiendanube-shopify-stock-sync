import os
import json
import time
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv
from src.store_config import StoreConfig
from src.shopify import ShopifyAPI
from src.tiendanube import TiendanubeAPI
from src.stock_tracker import StockTracker
from src.stock_database import StockDatabase
import logging
from collections import deque
from datetime import datetime, timedelta

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validar variables de entorno requeridas
required_env_vars = ['SHOPIFY_ACCESS_TOKEN', 'SHOPIFY_STORE_URL']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Faltan las siguientes variables de entorno: {', '.join(missing_vars)}")

# Inicializar el tracker de stock si estamos en modo validación
VALIDATE_STOCK = os.getenv('VALIDATE_STOCK', 'true').lower() == 'true'
stock_tracker = StockTracker() if VALIDATE_STOCK else None

# Inicializar la base de datos de stock
stock_db = StockDatabase()

class RequestQueue:
    def __init__(self, requests_per_second: int = 2):
        self.requests_per_second = requests_per_second
        self.last_request_time = None
        
    def wait_if_needed(self):
        """Espera si es necesario para respetar el límite de velocidad"""
        if self.last_request_time:
            elapsed = datetime.now() - self.last_request_time
            if elapsed.total_seconds() < (1 / self.requests_per_second):
                time.sleep((1 / self.requests_per_second) - elapsed.total_seconds())
        self.last_request_time = datetime.now()

class InventorySync:
    def __init__(self, store_config: Dict):
        """
        Inicializa el sincronizador de inventario
        
        Args:
            store_config (Dict): Configuración de la tienda
        """
        self.store_config = store_config
        self.store_id = store_config['api_url'].split('/')[-1]
        
        # Inicializar API de Tiendanube
        self.tiendanube = TiendanubeAPI(
            api_url=store_config['api_url'],
            token=store_config['token'],
            user_agent=store_config['user_agent']
        )
        
        # Inicializar contadores
        self.productos_actualizados = 0
        self.productos_sin_cambios = 0
        self.productos_no_encontrados = 0
        self.variantes_creadas = 0
        
        # Cola de solicitudes para control de velocidad
        self.request_queue = RequestQueue()
        
        logger.info(f"Iniciando sincronización para tienda {self.store_id}")

    def _make_shopify_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Realiza una solicitud a la API de Shopify con manejo de errores y límites de velocidad
        
        Args:
            method (str): Método HTTP
            endpoint (str): Endpoint de la API
            **kwargs: Argumentos adicionales para la solicitud
            
        Returns:
            requests.Response: Respuesta de la API
            
        Raises:
            Exception: Si hay un error en la solicitud
        """
        try:
            self.request_queue.wait_if_needed()
            
            headers = {
                'X-Shopify-Access-Token': os.getenv('SHOPIFY_ACCESS_TOKEN'),
                'Content-Type': 'application/json'
            }
            
            url = f"{os.getenv('SHOPIFY_STORE_URL')}/admin/api/2023-01/{endpoint}"
            response = requests.request(method, url, headers=headers, **kwargs)
            
            if response.status_code not in [200, 201]:
                logger.error(f"Error en solicitud a Shopify: {response.status_code} - {response.text}")
                raise Exception(f"Error en solicitud a Shopify: {response.status_code}")
                
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red en solicitud a Shopify: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"Error inesperado en solicitud a Shopify: {str(e)}")
            raise

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
        try:
            # Convertir stock infinito (None) a 999
            if new_quantity is None:
                print(f"∞ Convirtiendo stock infinito a 999 para producto ID: {product_info['product_id']}-{product_info['variant_id']}")
                new_quantity = 999
            else:
                new_quantity = int(new_quantity)
            
            current_quantity = int(current_quantity) if current_quantity is not None else 0
            
            if current_quantity == new_quantity:
                print(f"ℹ️ Stock sin cambios para producto ID: {product_info['product_id']}-{product_info['variant_id']} (Stock: {current_quantity})")
                self.productos_sin_cambios += 1
                return False

            print(f"🔄 Actualizando stock para {product_info['product_id']}-{product_info['variant_id']}")
            print(f"   - Stock actual: {current_quantity}")
            print(f"   - Nuevo stock: {new_quantity}")
            print(f"   - Inventory item ID: {inventory_item_id}")
            print(f"   - Location ID: {location_id}")

            response = self._make_shopify_request(
                'POST',
                'inventory_levels/set.json',
                json={
                    'inventory_item_id': str(inventory_item_id),
                    'location_id': str(location_id),
                    'available': new_quantity
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Error en respuesta de Shopify: {response.text}")
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
        try:
            # Reiniciar contadores
            self.productos_actualizados = 0
            self.productos_sin_cambios = 0
            self.productos_no_encontrados = 0
            self.variantes_creadas = 0
            
            # Inicializar base de datos de stock
            stock_db = StockDatabase()
            
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
                            # Obtener datos históricos
                            last_record = stock_db.get_last_stock(self.store_id, sku)
                            shopify_data = shopify_sku_map[sku]
                            
                            # Obtener stock actual de Shopify
                            current_shopify_stock = self.get_shopify_inventory_level(
                                shopify_data['inventory_item_id'],
                                self.shop_location_id
                            )
                            
                            # Obtener stock actual de Tiendanube
                            current_tiendanube_stock = variant['stock'] if variant.get('stock') is not None else 999
                            
                            if last_record:
                                last_tiendanube_stock = last_record.get('current_tiendanube_stock')
                                last_shopify_stock = last_record.get('current_shopify_stock')
                                
                                print(f"\n🔄 Analizando producto {sku}:")
                                print(f"   Histórico - Tiendanube: {last_tiendanube_stock}, Shopify: {last_shopify_stock}")
                                print(f"   Actual    - Tiendanube: {current_tiendanube_stock}, Shopify: {current_shopify_stock}")
                                
                                # Caso 1: Stock igual en Tiendanube pero menor en Shopify
                                if (current_tiendanube_stock == last_tiendanube_stock and 
                                    current_shopify_stock < last_shopify_stock):
                                    print(f"📉 Stock reducido en Shopify, actualizando Tiendanube")
                                    # Actualizar Tiendanube
                                    self.tiendanube.update_variant_stock(product_id, variant_id, current_shopify_stock)
                                    current_tiendanube_stock = current_shopify_stock
                                
                                # Caso 2: Stock modificado en Tiendanube
                                elif current_tiendanube_stock != last_tiendanube_stock:
                                    print(f"📊 Stock modificado en Tiendanube, actualizando Shopify")
                                    if current_tiendanube_stock is None:
                                        current_tiendanube_stock = 999
                                        print(f"∞ Convirtiendo stock infinito a 999")
                                    
                                    # Actualizar Shopify
                                    self.set_shopify_inventory(
                                        shopify_data['inventory_item_id'],
                                        self.shop_location_id,
                                        current_tiendanube_stock,
                                        current_shopify_stock,
                                        shopify_data
                                    )
                            
                            # Actualizar registro en la base de datos
                            stock_db.update_stock(
                                self.store_id,
                                sku,
                                current_tiendanube_stock,
                                current_shopify_stock
                            )
                            
                        else:
                            # Intentar crear la variante
                            print(f"🔄 Variante no encontrada, intentando crearla - SKU: {sku}")
                            shopify_product = self.find_shopify_product_by_tiendanube_id(product_id)
                            
                            if shopify_product:
                                try:
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

            print("\n✅ Sincronización completada")
            print(f"📊 Resumen de la tienda:")
            print(f"- Productos actualizados: {self.productos_actualizados}")
            print(f"- Productos sin cambios: {self.productos_sin_cambios}")
            print(f"- Productos no encontrados: {self.productos_no_encontrados}")
            print(f"- Variantes nuevas creadas: {self.variantes_creadas}")

        except Exception as e:
            print(f"❌ Error al sincronizar inventario: {str(e)}")
            raise

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
    """
    Función principal para sincronizar inventario
    
    Args:
        store_config (Dict): Configuración de la tienda
    """
    try:
        sync = InventorySync(store_config)
        sync.sync_inventory()
        
        logger.info("\n" + "="*50)
        logger.info("📊 Resumen de sincronización:")
        logger.info(f"✅ Productos actualizados: {sync.productos_actualizados}")
        logger.info(f"ℹ️ Productos sin cambios: {sync.productos_sin_cambios}")
        logger.info(f"❌ Productos no encontrados: {sync.productos_no_encontrados}")
        logger.info(f"🆕 Variantes nuevas creadas: {sync.variantes_creadas}")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"Error en sincronización: {str(e)}")
        raise

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