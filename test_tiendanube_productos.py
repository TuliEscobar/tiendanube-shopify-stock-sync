from Tiendanube import Tiendanube
from settings import TIENDANUBE_CREDENTIALS
import json
import requests
from datetime import datetime

def probar_tiendanube():
    print("Iniciando prueba de Tiendanube...")
    
    # Crear estructura para almacenar todos los datos
    todos_los_datos = {
        "fecha_descarga": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tiendas": []
    }
    
    try:
        # Probar cada tienda individualmente
        for i, credencial in enumerate(TIENDANUBE_CREDENTIALS, 1):
            print(f"\n{'='*70}")
            tienda_id = credencial['base_url'].split('/')[-1]
            print(f"Probando Tienda #{i} - ID: {tienda_id}")
            print(f"{'='*70}")
            
            # Crear instancia de Tiendanube con una sola credencial
            tienda = Tiendanube([credencial])
            
            # Datos de esta tienda
            datos_tienda = {
                "tienda_id": tienda_id,
                "productos": [],
                "total_productos": 0,
                "total_variantes": 0
            }
            
            try:
                # Obtener productos y variantes
                print("\nObteniendo productos...")
                productos = tienda.get_products()
                
                print("Obteniendo variantes...")
                variantes = tienda.get_variants()
                
                # Verificar productos
                if not productos:
                    print("No se encontraron productos en esta tienda")
                    datos_tienda["error"] = "No se encontraron productos"
                else:
                    print(f"\nSe encontraron {len(productos)} productos en esta tienda")
                    print(f"Se encontraron {len(variantes)} variantes en total")
                    
                    # Guardar productos en la estructura de datos
                    datos_tienda["productos"] = productos
                    datos_tienda["total_productos"] = len(productos)
                    datos_tienda["total_variantes"] = len(variantes)
                    
                    # Mostrar detalles de los primeros 3 productos como preview
                    print("\nPreview - Detalles de los primeros 3 productos:")
                    for producto in productos[:3]:
                        print("\n" + "-"*50)
                        print(f"ID Producto: {producto.get('id')}")
                        print(f"Nombre (ES): {producto.get('name', {}).get('es', 'Sin nombre')}")
                        print(f"Cantidad de variantes: {len(producto.get('variants', []))}")
                
            except requests.RequestException as e:
                error_msg = f"Error al conectar con la tienda: {str(e)}"
                print(error_msg)
                datos_tienda["error"] = error_msg
            
            # Agregar datos de esta tienda al conjunto total
            todos_los_datos["tiendas"].append(datos_tienda)
                
        # Guardar todos los datos en un solo archivo JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"productos_tiendanube_completo_{timestamp}.json"
        
        print(f"\n{'='*70}")
        print(f"Guardando todos los datos en {filename}")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(todos_los_datos, f, indent=2, ensure_ascii=False)
        print("Datos guardados exitosamente")
        
        # Mostrar resumen final
        print("\nRESUMEN:")
        for tienda in todos_los_datos["tiendas"]:
            print(f"Tienda {tienda['tienda_id']}:")
            print(f"  - Productos: {tienda['total_productos']}")
            print(f"  - Variantes: {tienda['total_variantes']}")
            if "error" in tienda:
                print(f"  - Error: {tienda['error']}")
                
    except Exception as e:
        print(f"Error durante la prueba: {str(e)}")

if __name__ == "__main__":
    probar_tiendanube() 