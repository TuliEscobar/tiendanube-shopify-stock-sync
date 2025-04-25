import os
from dotenv import load_dotenv
from src.store_config import StoreConfig
from src.shopify import ShopifyAPI
from src.tiendanube import TiendanubeAPI

def process_product_stock(product):
    """
    Procesa el stock de un producto y sus variantes
    
    Args:
        product (dict): Producto de Tiendanube
        
    Returns:
        dict: Producto con stock procesado
    """
    variants = product.get('variants', [])
    
    if variants:
        # Producto con variantes
        for variant in variants:
            if variant.get('stock') is None:
                print(f"🔄 Convirtiendo stock infinito a 999 para variante {variant['id']}")
                variant['stock'] = 999
                variant['sku'] = str(variant['id'])  # Asegurar que el SKU sea el ID de la variante
    else:
        # Producto sin variantes
        if product.get('stock') is None:
            print(f"🔄 Convirtiendo stock infinito a 999 para producto {product['id']}")
            product['stock'] = 999
        product['sku'] = str(product['id'])  # Asegurar que el SKU sea el ID del producto
        
    return product

def sync_store(store_config: dict, shopify: ShopifyAPI) -> int:
    """
    Sincroniza los productos de una tienda específica
    
    Args:
        store_config (dict): Configuración de la tienda
        shopify (ShopifyAPI): Instancia de ShopifyAPI
        
    Returns:
        int: Número de productos sincronizados
    """
    try:
        print(f"\n Procesando tienda")
        print(f" URL: {store_config['api_url']}")
        
        # Inicializar API de Tiendanube para esta tienda
        tiendanube = TiendanubeAPI(
            api_url=store_config['api_url'],
            token=store_config['token'],
            user_agent=store_config['user_agent']
        )
        
        # Obtener productos modificados recientemente
        print(f"\n🔍 Buscando productos modificados recientemente...")
        productos = tiendanube.get_products()
        
        if not productos:
            print(f"ℹ️ No se encontraron productos modificados recientemente")
            return 0
            
        print(f"✅ Se encontraron {len(productos)} productos modificados")
        
        productos_sincronizados = 0
        
        # Procesar cada producto
        for producto in productos:
            try:
                print(f"\n📦 Procesando producto:")
                print(f"   ID: {producto.get('id')}")
                print(f"   Nombre: {producto.get('name')}")
                print(f"   Última actualización: {producto.get('updated_at')}")
                
                # Procesar stock y SKUs
                producto = process_product_stock(producto)
                
                # Sincronizar con Shopify
                print(f"🔄 Sincronizando producto {producto['id']}...")
                if shopify.sync_products_from_tiendanube(producto):
                    productos_sincronizados += 1
                    print(f"✅ Producto sincronizado correctamente")
                
            except Exception as e:
                print(f"❌ Error sincronizando producto {producto.get('id')}: {str(e)}")
                continue
                
        print(f"\n✅ Sincronización completada para esta tienda")
        print(f"📊 Productos sincronizados: {productos_sincronizados}")
        
        return productos_sincronizados
        
    except Exception as e:
        print(f"❌ Error procesando tienda: {str(e)}")
        return 0

def main():
    """Función principal que sincroniza productos de múltiples tiendas a Shopify"""
    try:
        # Cargar configuración de tiendas
        store_config = StoreConfig()
        stores = store_config.get_all_stores()
        
        print(f"🔄 Procesando {len(stores)} tiendas...")
        
        # Inicializar Shopify API (una sola instancia para todas las tiendas)
        shopify = ShopifyAPI()
        
        # Estadísticas globales
        total_productos_sincronizados = 0
        
        # Procesar cada tienda
        for i, store in enumerate(stores, 1):
            print(f"\n📦 Tienda {i}/{len(stores)}")
            productos_sincronizados = sync_store(store, shopify)
            total_productos_sincronizados += productos_sincronizados
        
        # Resumen final
        print(f"\n🎉 Proceso completado!")
        print(f"📊 Total de productos sincronizados: {total_productos_sincronizados}")
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")

if __name__ == "__main__":
    main() 