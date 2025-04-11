import json
import os
from tiendanube import TiendanubeAPI
from shopify import ShopifyAPI
from dotenv import load_dotenv

def main():
    # Cargar variables de entorno
    load_dotenv()
    
    # Obtener todas las credenciales de Tiendanube
    tiendanube_credentials = json.loads(os.getenv('TIENDANUBE_CREDENTIALS', '[]').strip("'"))
    if not tiendanube_credentials:
        raise Exception("No se encontraron credenciales de Tiendanube")
    
    # Inicializar Shopify API (es el mismo para todas las tiendas)
    shopify = ShopifyAPI()
    
    print(f"🔄 Procesando {len(tiendanube_credentials)} tiendas...")
    
    # Estadísticas globales
    total_productos_sincronizados = 0
    
    # Procesar cada tienda
    for i, credentials in enumerate(tiendanube_credentials, 1):
        try:
            print(f"\n📦 Procesando tienda {i}/{len(tiendanube_credentials)}")
            print(f"🔹 URL: {credentials['base_url']}")
            
            # Inicializar API de Tiendanube con las credenciales actuales
            tiendanube = TiendanubeAPI(credentials)
            
            # Obtener productos de Tiendanube
            print("Obteniendo productos de Tiendanube...")
            tiendanube_products = tiendanube.get_products()
            print(f"Se encontraron {len(tiendanube_products)} productos en Tiendanube")
            
            # Sincronizar productos a Shopify
            print("\nIniciando sincronización con Shopify...")
            created_products = shopify.sync_products_from_tiendanube(tiendanube_products)
            
            print(f"\n✅ Sincronización completada para tienda {i}!")
            print(f"Total de productos sincronizados en esta tienda: {len(created_products)}")
            
            total_productos_sincronizados += len(created_products)
            
        except Exception as e:
            print(f"❌ Error durante la sincronización de la tienda {i}: {e}")
            continue
    
    print(f"\n🎉 Proceso completado!")
    print(f"Total de productos sincronizados en todas las tiendas: {total_productos_sincronizados}")

if __name__ == "__main__":
    main() 