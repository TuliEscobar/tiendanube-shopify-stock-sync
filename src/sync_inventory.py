import os
import json
import time
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
        
        # Control de rate limits
        self.last_request_time = time.time()
        self.min_request_interval = 0.5  # 500ms entre llamadas
        
        # Contadores
        self.productos_actualizados = 0
        self.productos_sin_cambios = 0
        self.productos_no_encontrados = 0
        
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

    def sync_inventory(self):
        """Sincroniza el inventario desde Tiendanube hacia Shopify"""
        try:
            print("\n🔄 Iniciando sincronización de inventario...")
            
            # Reiniciar contadores
            self.productos_actualizados = 0
            self.productos_sin_cambios = 0
            self.productos_no_encontrados = 0
            self.variantes_creadas = 0  # Nuevo contador
            
            # 1. Obtener productos de Tiendanube
            tiendanube_products = self.get_tiendanube_products()
            
            # 2. Obtener productos de Shopify
            shopify_products = self.get_shopify_products()
            
            # 3. Obtener ubicación principal de Shopify
            locations = self.get_shopify_locations()
            shop_location = next((loc for loc in locations if loc['name'] == 'Shop location'), None)
            if not shop_location:
                raise Exception("No se encontró la ubicación 'Shop location'")
            
            shop_location_id = shop_location['id']
            
            # 4. Crear mapeo de SKUs y productos de Shopify
            shopify_sku_map = {}
            shopify_product_map = {}  # Nuevo mapeo para productos completos
            for product in shopify_products:
                shopify_product_map[product['id']] = product
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
                                shop_location_id
                            )
                            
                            if self.set_shopify_inventory(
                                shopify_data['inventory_item_id'],
                                shop_location_id,
                                variant['stock'],
                                current_stock,
                                shopify_data
                            ):
                                self.productos_actualizados += 1
                            else:
                                self.productos_sin_cambios += 1
                        else:
                            # Intentar encontrar el producto principal por otras variantes
                            existing_product_id = None
                            for existing_sku, data in shopify_sku_map.items():
                                if existing_sku.startswith(product_id + '-'):
                                    existing_product_id = data['product_id']
                                    break
                            
                            if existing_product_id:
                                # Crear nueva variante en producto existente
                                try:
                                    shopify_product = shopify_product_map[existing_product_id]
                                    variant_data = {
                                        'price': str(variant.get('price', 0)),
                                        'sku': sku,
                                        'inventory_management': 'shopify',
                                        'inventory_policy': 'deny'
                                    }
                                    
                                    # Agregar opciones si existen
                                    for i, value in enumerate(variant.get('values', []), 1):
                                        if i <= len(product.get('attributes', [])):
                                            option_value = value.get('es', '')
                                            if option_value:
                                                variant_data[f'option{i}'] = option_value
                                    
                                    new_variant = self.create_variant(existing_product_id, variant_data)
                                    print(f"✅ Nueva variante creada - SKU: {sku}")
                                    self.variantes_creadas += 1
                                    
                                    # Actualizar mapeo de SKUs con la nueva variante
                                    shopify_sku_map[sku] = {
                                        'inventory_item_id': new_variant['inventory_item_id'],
                                        'product_id': existing_product_id,
                                        'variant_id': new_variant['id']
                                    }

                                    # Actualizar el inventario de la nueva variante
                                    if self.set_shopify_inventory(
                                        new_variant['inventory_item_id'],
                                        shop_location_id,
                                        variant.get('stock', 0),
                                        0,  # El stock inicial es 0 para una nueva variante
                                        {'product_id': existing_product_id, 'variant_id': new_variant['id']}
                                    ):
                                        self.productos_actualizados += 1
                                except Exception as e:
                                    print(f"❌ Error al crear nueva variante - SKU: {sku}: {str(e)}")
                                    self.productos_no_encontrados += 1
                            else:
                                print(f"❌ Producto no encontrado en Shopify - SKU: {sku}")
                                self.productos_no_encontrados += 1
                else:
                    # Producto simple
                    sku = product_id
                    if sku in shopify_sku_map:
                        shopify_data = shopify_sku_map[sku]
                        current_stock = self.get_shopify_inventory_level(
                            shopify_data['inventory_item_id'],
                            shop_location_id
                        )
                        
                        if self.set_shopify_inventory(
                            shopify_data['inventory_item_id'],
                            shop_location_id,
                            product.get('stock', 0),
                            current_stock,
                            shopify_data
                        ):
                            self.productos_actualizados += 1
                        else:
                            self.productos_sin_cambios += 1
                    else:
                        print(f"❌ Producto no encontrado en Shopify - SKU: {sku}")
                        self.productos_no_encontrados += 1

            print("\n✅ Sincronización completada")
            print(f"📊 Resumen de la tienda:")
            print(f"- Productos actualizados: {self.productos_actualizados}")
            print(f"- Productos sin cambios: {self.productos_sin_cambios}")
            print(f"- Productos no encontrados: {self.productos_no_encontrados}")
            print(f"- Nuevas variantes creadas: {self.variantes_creadas}")

        except Exception as e:
            print(f"\n❌ Error durante la sincronización: {str(e)}")
            raise

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