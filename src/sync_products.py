import json
import os
from src.tiendanube import TiendanubeAPI
from src.shopify import ShopifyAPI
from src.store_config import StoreConfig
from dotenv import load_dotenv

def process_product_stock(product):
    """
    Procesa el stock de un producto y sus variantes.
    Convierte stock null (infinito) a 999.
    """
    # Procesar variantes
    if 'variants' in product:
        for variant in product['variants']:
            if variant.get('stock') is None:
                print(f"  ∞ Convirtiendo stock infinito a 999 para variante {variant.get('id')}")
                variant['stock'] = 999
    return product

def main():
    # Cargar variables de entorno
    load_dotenv()
    
    # Inicializar la configuración de tiendas desde .env
    store_config = StoreConfig()
    stores = store_config.get_all_stores()
    
    # Inicializar Shopify API (es el mismo para todas las tiendas)
    shopify = ShopifyAPI()
    
    print(f"🔄 Procesando {len(stores)} tiendas...")
    
    # Estadísticas globales
    total_productos_sincronizados = 0
    total_productos_stock_infinito = 0
    
    # Procesar cada tienda
    for i, store in enumerate(stores, 1):
        try:
            print(f"\n📦 Procesando tienda {i}/{len(stores)}")
            print(f"🔹 URL: {store['api_url']}")
            print(f"🔹 Categoría: {store['category']}")
            
            # Inicializar API de Tiendanube con la URL de la tienda
            tiendanube = TiendanubeAPI(
                api_url=store['api_url'],
                token=store['token'],
                user_agent=store['user_agent']
            )
            
            # Obtener productos de Tiendanube
            print("Obteniendo productos de Tiendanube...")
            tiendanube_products = tiendanube.get_products()
            
            # Procesar cada producto
            print("\nProcesando productos...")
            productos_sincronizados = 0
            
            for product in tiendanube_products:
                try:
                    # Procesar stock infinito
                    product = process_product_stock(product)
                    # Agregar información de remarcas
                    product['markups'] = store.get('markups', {})
                    
                    # Sincronizar producto individual con Shopify
                    if shopify.sync_products_from_tiendanube(product):
                        productos_sincronizados += 1
                        print(f"✅ Producto {product.get('id')} sincronizado correctamente")
                    else:
                        print(f"❌ Error al sincronizar producto {product.get('id')}")
                        
                except Exception as e:
                    print(f"❌ Error procesando producto {product.get('id')}: {e}")
                    continue
            
            print(f"\n✅ Sincronización completada para tienda {i}!")
            print(f"Total de productos sincronizados en esta tienda: {productos_sincronizados}")
            
            total_productos_sincronizados += productos_sincronizados
            
        except Exception as e:
            print(f"❌ Error procesando tienda {i}: {e}")
            continue
    
    print(f"\n🎉 Proceso completado!")
    print(f"Total de productos sincronizados: {total_productos_sincronizados}")

if __name__ == '__main__':
    main() 