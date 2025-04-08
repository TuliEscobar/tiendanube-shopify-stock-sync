from src.tiendanube import TiendanubeAPI, TIENDANUBE_CREDENTIALS

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
            print(f"    Stock: {variant.get('stock')}")
    else:
        print("\nNo hay variantes disponibles")
    print("-" * 50)

def get_all_products(tienda):
    """Obtiene todos los productos de una tienda usando paginación"""
    page = 1
    all_products = []
    
    try:
        productos = tienda.get_products(page=page, per_page=50, include_variants=True)
        if productos:
            all_products.extend(productos)
    except Exception as e:
        print(f"Error al obtener productos: {e}")
    
    return all_products

def main():
    # Obtener productos de todas las tiendas configuradas
    total_tiendas = len(TIENDANUBE_CREDENTIALS)
    
    for store_number in range(1, total_tiendas + 1):
        print(f"\n{'='*20} Tienda {store_number} {'='*20}")
        try:
            # Crear instancia de la tienda
            tienda = TiendanubeAPI(store_number=store_number)
            
            # Obtener todos los productos con sus variantes
            productos = get_all_products(tienda)
            
            print(f"\nSe encontraron {len(productos)} productos:")
            for producto in productos:
                print_product_info(producto)
                
        except Exception as e:
            print(f"Error con la tienda {store_number}: {e}")

if __name__ == "__main__":
    main() 