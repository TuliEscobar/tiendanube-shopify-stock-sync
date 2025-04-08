from tiendanube import TiendanubeAPI
from shopify import ShopifyAPI

def main():
    # Inicializar APIs
    tiendanube = TiendanubeAPI()
    shopify = ShopifyAPI()
    
    try:
        # Obtener productos de Tiendanube
        print("Obteniendo productos de Tiendanube...")
        tiendanube_products = tiendanube.get_products()
        print(f"Se encontraron {len(tiendanube_products)} productos en Tiendanube")
        
        # Sincronizar productos a Shopify
        print("\nIniciando sincronización con Shopify...")
        created_products = shopify.sync_products_from_tiendanube(tiendanube_products)
        
        print(f"\nSincronización completada!")
        print(f"Total de productos sincronizados: {len(created_products)}")
        
    except Exception as e:
        print(f"Error durante la sincronización: {e}")

if __name__ == "__main__":
    main() 