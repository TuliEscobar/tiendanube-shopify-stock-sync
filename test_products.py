import sys
from pathlib import Path

# Agregar el directorio src al path de Python
sys.path.append(str(Path(__file__).parent))

from src.tiendanube import TiendanubeAPI
from src.store_config import StoreConfig

def print_product_info(product):
    """Imprime la información de un producto y sus variantes"""
    print(f"\nProducto ID: {product.get('id')}")
    print(f"Nombre: {product.get('name', {}).get('es', 'Sin nombre')}")
    print(f"SKU: {product.get('sku', 'Sin SKU')}")
    
    # Imprimir información de variantes
    variants = product.get('variants', [])
    if variants:
        print("\nVariantes:")
        for variant in variants:
            print(f"  - ID: {variant.get('id')}")
            print(f"    SKU: {variant.get('sku', 'Sin SKU')}")
            print(f"    Precio: ${variant.get('price')}")
            
            # Verificar si el stock es infinito
            stock = variant.get('stock')
            if stock is None:
                print(f"    Stock: ∞ (Infinito)")
            else:
                print(f"    Stock: {stock}")
    else:
        print("\nNo hay variantes disponibles")
    print("-" * 50)

def get_all_products(tienda):
    """Obtiene todos los productos de una tienda"""
    return tienda.get_products()

def main():
    # Inicializar la configuración de tiendas desde .env
    store_config = StoreConfig()
    stores = store_config.get_all_stores()
    
    print(f"Se encontraron {len(stores)} tiendas configuradas")
    
    for i, store in enumerate(stores, 1):
        print(f"\n{'='*20} Tienda {i} {'='*20}")
        print(f"URL: {store['api_url']}")
        print(f"Categoría: {store.get('category', 'No especificada')}")
        
        try:
            # Crear instancia de la tienda con las credenciales completas
            tienda = TiendanubeAPI(
                api_url=store['api_url'],
                token=store['token'],
                user_agent=store['user_agent']
            )
            
            # Obtener todos los productos con sus variantes
            productos = get_all_products(tienda)
            
            print(f"\nSe encontraron {len(productos)} productos:")
            for producto in productos:
                print_product_info(producto)
                
        except Exception as e:
            print(f"Error con la tienda {i}: {e}")

if __name__ == "__main__":
    main() 