import json
import os
from src.tiendanube import TiendanubeAPI
from src.shopify import ShopifyAPI
from src.store_config import StoreConfig
from dotenv import load_dotenv

def main():
    # Cargar variables de entorno
    load_dotenv()
    
    # Inicializar la configuración de tiendas desde Excel
    store_config = StoreConfig()
    stores = store_config.get_all_stores()
    
    # Inicializar Shopify API (es el mismo para todas las tiendas)
    shopify = ShopifyAPI()
    
    print(f"🔄 Procesando {len(stores)} tiendas...")
    
    # Estadísticas globales
    total_productos_sincronizados = 0
    
    # Procesar cada tienda
    for i, store in enumerate(stores, 1):
        try:
            print(f"\n📦 Procesando tienda {i}/{len(stores)}")
            print(f"🔹 URL: {store['api_url']}")
            print(f"🔹 Categoría: {store['category']}")
            
            # Inicializar API de Tiendanube con la URL de la tienda
            tiendanube = TiendanubeAPI(api_url=store['api_url'])
            
            # Obtener productos de Tiendanube
            print("Obteniendo productos de Tiendanube...")
            tiendanube_products = tiendanube.get_products()
            
            # Agregar información de remarcas a los productos
            for product in tiendanube_products:
                product['markups'] = store['markups']
            
            print(f"Se encontraron {len(tiendanube_products)} productos en Tiendanube")
            
            # Sincronizar productos a Shopify
            print("\nIniciando sincronización con Shopify...")
            created_products = shopify.sync_products_from_tiendanube(tiendanube_products)
            
            print(f"\n✅ Sincronización completada para tienda {i}!")
            print(f"Total de productos sincronizados en esta tienda: {len(created_products)}")
            
            total_productos_sincronizados += len(created_products)
            
        except Exception as e:
            print(f"❌ Error procesando tienda {i}: {e}")
            continue
    
    print(f"\n🎉 Proceso completado!")
    print(f"Total de productos sincronizados: {total_productos_sincronizados}")

if __name__ == '__main__':
    main() 