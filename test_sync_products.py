import os
import json
from dotenv import load_dotenv
from src.tiendanube import TiendanubeAPI
from src.shopify import ShopifyAPI

def main():
    # Cargar variables de entorno
    load_dotenv('src/.env')
    
    try:
        # Inicializar APIs
        tiendanube = TiendanubeAPI(store_number=1)
        shopify = ShopifyAPI()
        
        # Obtener productos de Tiendanube
        tiendanube_products = tiendanube.get_products()
        print(f"\nProductos encontrados en Tiendanube: {len(tiendanube_products)}")
        
        # Imprimir detalles completos de cada producto
        for product in tiendanube_products:
            print("\nDetalles del producto de Tiendanube:")
            print(json.dumps(product, indent=2, ensure_ascii=False))
            
        # Sincronizar productos
        print("\nIniciando sincronización con Shopify...")
        shopify_products = shopify.sync_products_from_tiendanube(tiendanube_products)
        
        print(f"\nProductos sincronizados exitosamente: {len(shopify_products)}")
        
    except Exception as e:
        print(f"Error durante la sincronización: {e}")

if __name__ == "__main__":
    main() 