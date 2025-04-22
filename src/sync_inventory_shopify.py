import os
import json
import time
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv
from src.store_config import StoreConfig
from src.shopify import ShopifyAPI

# Cargar variables de entorno
load_dotenv()

class InventorySyncFromShopify:
    def __init__(self, store_config: Dict):
        """
        Inicializa el sincronizador de inventario desde Shopify
        
        Args:
            store_config (Dict): Configuración de la tienda desde el Excel
        """
        # Configuración de Tiendanube
        self.tiendanube_base_url = store_config['api_url']
        self.tiendanube_headers = {
            'User-Agent': store_config['user_agent'],
            'Content-Type': 'application/json',
            'Authentication': store_config['token']
        }
        
        # Inicializar Shopify API
        self.shopify = ShopifyAPI()
        self.shopify_headers = self.shopify.headers
        self.shopify_store_url = self.shopify.api_url
        
        # Control de rate limits
        self.last_request_time = time.time()
        self.min_request_interval = 0.5
        
        # Contadores
        self.productos_actualizados = 0
        self.productos_sin_cambios = 0
        self.productos_no_encontrados = 0

    def _wait_for_rate_limit(self):
        """Espera el tiempo necesario para respetar el rate limit"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _make_shopify_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Realiza una petición a la API de Shopify"""
        self._wait_for_rate_limit()
        url = f'{self.shopify_store_url}/{endpoint}'
        response = requests.request(
            method=method,
            url=url,
            headers=self.shopify_headers,
            **kwargs
        )
        return response

    def get_tiendanube_product_by_sku(self, sku: str) -> Optional[Dict]:
        """Obtiene un producto de Tiendanube por su SKU"""
        try:
            tiendanube_id = sku.split('-')[0]  # Obtener el ID de Tiendanube del SKU
            url = f'{self.tiendanube_base_url}/products/{tiendanube_id}'
            response = requests.get(url, headers=self.tiendanube_headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                raise Exception('Error al obtener producto')
                
        except Exception as e:
            print(f"❌ Error al buscar producto en Tiendanube: {str(e)}")
            return None

    def update_tiendanube_stock(self, product_id: str, variant_id: str, new_stock: int) -> bool:
        """
        Actualiza el stock de una variante en Tiendanube
        
        Args:
            product_id (str): ID del producto en Tiendanube
            variant_id (str): ID de la variante en Tiendanube
            new_stock (int): Nuevo valor de stock
            
        Returns:
            bool: True si se actualizó el stock, False si no hubo cambios
        """
        try:
            # 1. Obtener el stock actual
            url = f'{self.tiendanube_base_url}/products/{product_id}/variants/{variant_id}'
            response = requests.get(url, headers=self.tiendanube_headers)
            
            if response.status_code != 200:
                raise Exception('Error al obtener variante')
            
            variant_data = response.json()
            current_stock = variant_data.get('stock', 0)
            
            # 2. Si el stock es diferente, actualizarlo
            if current_stock != new_stock:
                update_data = {'stock': new_stock}
                response = requests.put(
                    url,
                    headers=self.tiendanube_headers,
                    json=update_data
                )
                
                if response.status_code != 200:
                    raise Exception('Error al actualizar stock')
                    
                return True
                
            return False
            
        except Exception as e:
            print(f"❌ Error al actualizar stock en Tiendanube: {str(e)}")
            return False

    def sync_inventory_from_shopify(self):
        """
        Sincroniza el inventario desde Shopify hacia Tiendanube.
        Si el stock en Shopify es menor que en Tiendanube, actualiza Tiendanube
        para igualar al stock menor de Shopify.
        """
        try:
            # 1. Obtener productos de Shopify
            response = self._make_shopify_request(
                'GET',
                'products.json',
                params={'limit': 250, 'fields': 'id,variants'}
            )
            
            if response.status_code != 200:
                raise Exception('Error al obtener productos de Shopify')
            
            shopify_products = response.json()['products']
            
            # 2. Obtener ubicación principal de Shopify
            response = self._make_shopify_request('GET', 'locations.json')
            if response.status_code != 200:
                raise Exception('Error al obtener ubicaciones')
            
            locations = response.json()['locations']
            shop_location = next((loc for loc in locations if loc['name'] == 'Shop location'), None)
            if not shop_location:
                raise Exception("No se encontró la ubicación 'Shop location'")
            
            # 3. Procesar cada producto y sus variantes
            for product in shopify_products:
                for variant in product.get('variants', []):
                    sku = variant.get('sku')
                    if not sku:
                        continue
                    
                    # Obtener el stock actual en Shopify
                    response = self._make_shopify_request(
                        'GET',
                        'inventory_levels.json',
                        params={
                            'inventory_item_ids': variant['inventory_item_id'],
                            'location_ids': shop_location['id']
                        }
                    )
                    
                    if response.status_code != 200:
                        continue
                    
                    inventory_levels = response.json().get('inventory_levels', [])
                    if not inventory_levels:
                        continue
                    
                    shopify_stock = inventory_levels[0].get('available', 0)
                    
                    # Buscar y comparar con Tiendanube
                    tiendanube_product = self.get_tiendanube_product_by_sku(sku)
                    if tiendanube_product:
                        tiendanube_id = str(tiendanube_product['id'])
                        variant_id = sku.split('-')[1] if '-' in sku else None
                        
                        if variant_id:
                            # Obtener el stock actual en Tiendanube
                            url = f'{self.tiendanube_base_url}/products/{tiendanube_id}/variants/{variant_id}'
                            response = requests.get(url, headers=self.tiendanube_headers)
                            
                            if response.status_code == 200:
                                tiendanube_variant = response.json()
                                tiendanube_stock = tiendanube_variant.get('stock', 0)
                                
                                # Si el stock de Shopify es menor, actualizar Tiendanube
                                if shopify_stock < tiendanube_stock:
                                    print(f"⚠️ Stock en Shopify menor - SKU: {sku}")
                                    print(f"   Shopify: {shopify_stock} | Tiendanube: {tiendanube_stock}")
                                    
                                    # Actualizar Tiendanube al stock menor de Shopify
                                    if self.update_tiendanube_stock(tiendanube_id, variant_id, shopify_stock):
                                        self.productos_actualizados += 1
                                        print(f"✅ Stock de Tiendanube reducido a {shopify_stock}")
                                    else:
                                        print("❌ Error al actualizar stock en Tiendanube")
                                else:
                                    self.productos_sin_cambios += 1
                        else:
                            self.productos_no_encontrados += 1
                    else:
                        self.productos_no_encontrados += 1
            
        except Exception as e:
            print(f"❌ Error durante la sincronización: {str(e)}")
            raise

def main():
    try:
        # Inicializar la configuración de tiendas desde Excel
        store_config = StoreConfig()
        stores = store_config.get_all_stores()
        
        if not stores:
            print("❌ No se encontraron tiendas configuradas")
            return
        
        # Estadísticas globales
        total_actualizados = 0
        total_sin_cambios = 0
        total_no_encontrados = 0
        
        # Procesar cada tienda
        for i, store in enumerate(stores, 1):
            try:
                sync = InventorySyncFromShopify(store)
                sync.sync_inventory_from_shopify()
                
                # Acumular estadísticas
                total_actualizados += sync.productos_actualizados
                total_sin_cambios += sync.productos_sin_cambios
                total_no_encontrados += sync.productos_no_encontrados
                
                # Esperar entre tiendas
                if i < len(stores):
                    time.sleep(5)
                
            except Exception as e:
                print(f"❌ Error en tienda {i}: {str(e)}")
                continue
        
        print("\n📊 Resumen:")
        print(f"- Productos actualizados: {total_actualizados}")
        print(f"- Productos sin cambios: {total_sin_cambios}")
        print(f"- Productos no encontrados: {total_no_encontrados}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 