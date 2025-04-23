import schedule
import time
import subprocess
import sys
from datetime import datetime
import os
from dotenv import load_dotenv
import json
from typing import Dict, Optional

def log_message(message: str):
    """Función para loggear mensajes con timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()  # Forzar la salida inmediata

class StockTracker:
    def __init__(self):
        self.cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_cache.json')
        self.last_stocks = self._load_cache()
        log_message(f"StockTracker inicializado. Cache: {self.cache_file}")
    
    def _load_cache(self) -> Dict:
        """Carga el último estado conocido del stock desde el archivo cache"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    log_message(f"Cache cargado exitosamente con {len(data)} registros")
                    return data
            except Exception as e:
                log_message(f"Error al cargar cache: {e}")
                return {}
        log_message("Cache no encontrado, iniciando nuevo")
        return {}
    
    def _save_cache(self):
        """Guarda el estado actual del stock en el archivo cache"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.last_stocks, f, indent=2)
            log_message("Cache guardado exitosamente")
        except Exception as e:
            log_message(f"Error al guardar cache: {e}")
    
    def get_last_stock(self, store_id: str, product_id: str) -> Optional[int]:
        """Obtiene el último stock conocido de un producto"""
        store_data = self.last_stocks.get(store_id, {})
        stock = store_data.get(product_id)
        log_message(f"Obteniendo stock para tienda {store_id}, producto {product_id}: {stock}")
        return stock
    
    def update_stock(self, store_id: str, product_id: str, stock: int):
        """Actualiza el stock de un producto en el cache"""
        if store_id not in self.last_stocks:
            self.last_stocks[store_id] = {}
        self.last_stocks[store_id][product_id] = stock
        log_message(f"Actualizando stock para tienda {store_id}, producto {product_id}: {stock}")
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
    log_message(f"🔄 Iniciando ejecución de {script_name}")
    
    try:
        # Obtener la ruta del directorio actual
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, script_name)
        log_message(f"Ruta del script: {script_path}")
        
        # Configurar el entorno para UTF-8
        my_env = os.environ.copy()
        my_env["PYTHONIOENCODING"] = "utf-8"
        my_env["STOCK_VALIDATION"] = "1"  # Flag para indicar que se debe validar el stock
        
        log_message("Ejecutando script...")
        # Ejecutar el script y capturar toda la salida
        process = subprocess.run(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            env=my_env
        )
        
        log_message("Salida del script:")
        # Mostrar la salida
        print(process.stdout)
        
        if process.returncode == 0:
            log_message(f"✅ {script_name} completado exitosamente")
        else:
            log_message(f"❌ Error en {script_name}:")
            print(process.stderr)
        
        return process
                
    except Exception as e:
        log_message(f"❌ Error crítico al ejecutar {script_name}: {e}")
        raise

def run_sync_inventory():
    """
    Ejecuta la sincronización de Tiendanube a Shopify
    
    Returns:
        bool: True si no hubo cambios en Tiendanube, False si hubo cambios
    """
    log_message("Iniciando sincronización Tiendanube → Shopify")
    process = run_sync_script('sync_inventory.py')
    result = process.returncode == 0 and "Stock sin cambios" in process.stdout
    log_message(f"Resultado sincronización: {'Sin cambios' if result else 'Con cambios'}")
    return result

def run_sync_inventory_from_shopify():
    """Ejecuta la sincronización de Shopify a Tiendanube"""
    log_message("Iniciando sincronización Shopify → Tiendanube")
    run_sync_script('sync_inventory_shopify.py')

def run_both_syncs():
    """
    Ejecuta las sincronizaciones en el siguiente orden:
    1. Verifica cambios en Tiendanube y actualiza Shopify si es necesario
    2. Si no hubo cambios en Tiendanube, verifica Shopify y actualiza Tiendanube si hay menos stock
    """
    log_message("🔄 INICIANDO CICLO DE SINCRONIZACIÓN BIDIRECCIONAL")
    
    try:
        log_message("1️⃣ Verificando cambios en Tiendanube...")
        no_changes_in_tiendanube = run_sync_inventory()
        
        if no_changes_in_tiendanube:
            log_message("2️⃣ No hay cambios en Tiendanube. Verificando Shopify...")
            time.sleep(5)  # Esperar 5 segundos entre sincronizaciones
            run_sync_inventory_from_shopify()
        else:
            log_message("⏭️ Se detectaron cambios en Tiendanube, omitiendo verificación de Shopify")
        
        log_message("✅ CICLO DE SINCRONIZACIÓN COMPLETADO")
        
    except Exception as e:
        log_message(f"❌ ERROR EN CICLO DE SINCRONIZACIÓN: {e}")

def main():
    # Configurar salida UTF-8 para Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    # Cargar variables de entorno
    load_dotenv()
    
    log_message("🚀 INICIANDO SCHEDULER DE SINCRONIZACIÓN BIDIRECCIONAL")
    log_message("⏰ Configurado para ejecutar cada 15 minutos")
    
    try:
        log_message("Ejecutando sincronización inicial...")
        run_both_syncs()
        
        # Programar la ejecución cada 15 minutos
        schedule.every(15).minutes.do(run_both_syncs)
        log_message("Scheduler configurado y en ejecución")
        
        # Mantener el script corriendo
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                log_message("⛔ Deteniendo scheduler por solicitud del usuario")
                break
            except Exception as e:
                log_message(f"⚠️ Error en ciclo del scheduler: {e}")
                time.sleep(60)  # Esperar 1 minuto antes de reintentar
    
    except Exception as e:
        log_message(f"❌ ERROR CRÍTICO EN SCHEDULER: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 