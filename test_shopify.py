from src.shopify import ShopifyAPI
from dotenv import load_dotenv
import os

def main():
    # Cargar variables de entorno desde src/.env
    load_dotenv('src/.env')
    
    # Obtener credenciales
    shop_url = os.getenv('SHOPIFY_SHOP_URL')
    access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
    
    if not shop_url or not access_token:
        print("Error: Faltan credenciales de Shopify en el archivo .env")
        return
    
    try:
        # Inicializar API
        shopify_api = ShopifyAPI(shop_url=shop_url, access_token=access_token)
        
        # Intentar obtener productos
        print("\nCredenciales configuradas:")
        print(f"URL: {shop_url}")
        print(f"Token: {access_token[:10]}...{access_token[-4:]}")
        
        print("\nObteniendo productos de Shopify...")
        products = shopify_api.get_products()
        
        print(f"\nSe encontraron {len(products)} productos:")
        for product in products:
            print(f"\nProducto ID: {product.get('id')}")
            print(f"Título: {product.get('title')}")
            print(f"Precio: ${product.get('variants', [{}])[0].get('price', 'N/A')}")
            print(f"SKU: {product.get('variants', [{}])[0].get('sku', 'No configurado')}")
            print(f"Stock: {product.get('variants', [{}])[0].get('inventory_quantity', 0)}")
            
            # Mostrar variantes si existen
            variants = product.get('variants', [])
            if len(variants) > 1:
                print("\nVariantes:")
                for variant in variants[1:]:  # Excluimos la primera variante que ya mostramos
                    print(f"- SKU: {variant.get('sku', 'No configurado')}")
                    print(f"  Precio: ${variant.get('price', 'N/A')}")
                    print(f"  Stock: {variant.get('inventory_quantity', 0)}")
        
    except Exception as e:
        print(f"Error al conectar con Shopify: {str(e)}")

if __name__ == "__main__":
    main() 