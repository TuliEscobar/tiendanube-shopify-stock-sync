import schedule
import time
import subprocess
import sys
from datetime import datetime
import os
from dotenv import load_dotenv
import json
from typing import Dict, Optional

class StockTracker:
    def __init__(self):
        self.cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_cache.json')
        self.last_stocks = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Carga el último estado conocido del stock desde el archivo cache"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Guarda el estado actual del stock en el archivo cache"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.last_stocks, f, indent=2)
    
    def get_last_stock(self, store_id: str, product_id: str) -> Optional[int]:
        """Obtiene el último stock conocido de un producto"""
        store_data = self.last_stocks.get(store_id, {})
        return store_data.get(product_id)
    
    def update_stock(self, store_id: str, product_id: str, stock: int):
        """Actualiza el stock de un producto en el cache"""
        if store_id not in self.last_stocks:
            self.last_stocks[store_id] = {}
        self.last_stocks[store_id][product_id] = stock
        self._save_cache()

# Variable global para el tracker de stock
stock_tracker = StockTracker()

def run_sync_script(script_name):
    """
    Ejecuta un script de sincronización
    
    Args:
        script_name (str): Nombre del script a ejecutar
        
    Returns:
        subprocess.CompletedProcess: Proceso completado con su salida
    """
    print(f"\nIniciando {script_name} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Obtener la ruta del directorio actual
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, script_name)
        
        # Configurar el entorno para UTF-8
        my_env = os.environ.copy()
        my_env["PYTHONIOENCODING"] = "utf-8"
        my_env["STOCK_VALIDATION"] = "1"  # Flag para indicar que se debe validar el stock
        
        # Ejecutar el script y capturar toda la salida
        process = subprocess.run(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            env=my_env
        )
        
        # Mostrar la salida
        print(process.stdout)
        
        if process.returncode == 0:
            print(f"[OK] {script_name} completado exitosamente")
        else:
            print(f"[ERROR] Error en {script_name}:")
            print(process.stderr)
        
        return process
                
    except Exception as e:
        print(f"[ERROR] Error al ejecutar {script_name}: {e}")
        raise

def run_sync_inventory():
    """
    Ejecuta la sincronización de Tiendanube a Shopify
    
    Returns:
        bool: True si no hubo cambios en Tiendanube, False si hubo cambios
    """
    process = run_sync_script('sync_inventory.py')
    return process.returncode == 0 and "Stock sin cambios" in process.stdout

def run_sync_inventory_from_shopify():
    """Ejecuta la sincronización de Shopify a Tiendanube"""
    run_sync_script('sync_inventory_shopify.py')

def run_both_syncs():
    """
    Ejecuta las sincronizaciones en el siguiente orden:
    1. Verifica cambios en Tiendanube y actualiza Shopify si es necesario
    2. Si no hubo cambios en Tiendanube, verifica Shopify y actualiza Tiendanube si hay menos stock
    """
    print("\n🔄 Iniciando proceso de sincronización...")
    
    # 1. Verificar Tiendanube primero
    print("\n1️⃣ Verificando cambios en Tiendanube...")
    no_changes_in_tiendanube = run_sync_inventory()
    
    # 2. Si no hubo cambios en Tiendanube, verificar Shopify
    if no_changes_in_tiendanube:
        print("\n2️⃣ No hay cambios en Tiendanube. Verificando Shopify...")
        time.sleep(5)  # Esperar 5 segundos entre sincronizaciones
        run_sync_inventory_from_shopify()
    else:
        print("\n⏭️ Se detectaron cambios en Tiendanube, omitiendo verificación de Shopify")
    
    print("\n✅ Proceso de sincronización completado")

def main():
    # Configurar salida UTF-8
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    # Cargar variables de entorno
    load_dotenv()
    
    print("[INFO] Iniciando programador de sincronización bidireccional")
    print("[INFO] Configurado para ejecutar cada 15 minutos")
    
    # Ejecutar inmediatamente al iniciar
    run_both_syncs()
    
    # Programar la ejecución cada 15 minutos
    schedule.every(15).minutes.do(run_both_syncs)
    
    # Mantener el script corriendo
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] Deteniendo el programador...")
            break
        except Exception as e:
            print(f"[ERROR] Error en el programador: {e}")
            # Esperar 5 minutos antes de reintentar en caso de error
            time.sleep(300)
            continue

if __name__ == "__main__":
    main() 