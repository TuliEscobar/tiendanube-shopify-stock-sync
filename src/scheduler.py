import os
import sys
import time
import schedule
import subprocess
from datetime import datetime
from dotenv import load_dotenv

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

def run_inventory_sync():
    """
    Ejecuta la sincronización de inventario y registra el resultado
    """
    try:
        print("\n[INFO] Ejecutando sincronización de inventario...")
        process = run_sync_script('sync_inventory.py')
        
        if process.returncode == 0:
            print("[INFO] Sincronización de inventario completada")
            # Registrar la última sincronización exitosa
            with open("last_sync.log", "a") as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Sync exitoso\n")
        else:
            print("[ERROR] Error en la sincronización de inventario")
            # Registrar el error
            with open("error_sync.log", "a") as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error en sync: {process.stderr}\n")
    
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
        with open("error_sync.log", "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error inesperado: {str(e)}\n")

def main():
    # Configurar salida UTF-8 para Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    # Cargar variables de entorno
    load_dotenv()
    
    print("[INFO] Iniciando programador de sincronización de inventario")
    print("[INFO] Configurado para ejecutar cada 15 minutos")
    
    # Ejecutar inmediatamente al iniciar
    run_inventory_sync()
    
    # Programar la ejecución cada 15 minutos
    schedule.every(15).minutes.do(run_inventory_sync)
    
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