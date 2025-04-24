import os
from dotenv import load_dotenv
from src.store_config import StoreConfig
from src.shopify import ShopifyAPI
from src.tiendanube import TiendanubeAPI

def process_product_stock(product):
    """
    Procesa el stock de un producto y sus variantes.
    Convierte stock infinito (None) a 999.
    """
    if product.get('variants'):
        for variant in product['variants']:
            if variant.get('stock') is None:
                print(f"∞ Convirtiendo stock infinito a 999 para variante ID: {variant['id']}")
                variant['stock'] = 999
    return product

def main():
    # Cargar variables de entorno
    load_dotenv()
    
    # Inicializar la configuración de tiendas desde .env
    store_config = StoreConfig()
    stores = store_config.get_all_stores()
    
    # Inicializar Shopify API
    shopify = ShopifyAPI()
    
    print(f"🔄 Procesando {len(stores)} tiendas...")
    
    # Estadísticas globales
    total_productos_actualizados = 0
    
    # Procesar cada tienda
    for i, store in enumerate(stores, 1):
        try:
            print(f"\n📦 Procesando tienda {i}/{len(stores)}")
            print(f"🔹 URL: {store['api_url']}")
            
            # Inicializar API de Tiendanube
            tiendanube = TiendanubeAPI(
                api_url=store['api_url'],
                token=store['token'],
                user_agent=store['user_agent']
            )
            
            # Obtener productos de Tiendanube
            print("\n🔄 Obteniendo productos de Tiendanube...")
            tiendanube_products = tiendanube.get_products()
            print(f"✅ Se encontraron {len(tiendanube_products)} productos")
            
            # Procesar cada producto
            productos_actualizados = 0
            
            for product in tiendanube_products:
                try:
                    # Procesar stock infinito
                    product = process_product_stock(product)
                    
                    # Sincronizar stock con Shopify
                    if shopify.sync_products_from_tiendanube(product):
                        productos_actualizados += 1
                        print(f"✅ Stock actualizado para producto {product.get('id')}")
                    
                except Exception as e:
                    print(f"❌ Error procesando producto {product.get('id')}: {e}")
                    continue
            
            print(f"\n✅ Sincronización completada para tienda {i}")
            print(f"📊 Productos actualizados en esta tienda: {productos_actualizados}")
            
            total_productos_actualizados += productos_actualizados
            
        except Exception as e:
            print(f"❌ Error procesando tienda {i}: {e}")
            continue
    
    print(f"\n🎉 Proceso completado!")
    print(f"📊 Total de productos actualizados: {total_productos_actualizados}")

if __name__ == "__main__":
    main() 