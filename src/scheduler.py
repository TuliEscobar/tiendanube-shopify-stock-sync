import schedule
import time
from datetime import datetime
import os
import sys
from src.sync_products import main as sync_products

def job():
    """Ejecuta la sincronización de stock"""
    print(f"\n🕒 Iniciando sincronización programada: {datetime.now()}")
    try:
        sync_products()
        print(f"✅ Sincronización completada: {datetime.now()}")
    except Exception as e:
        print(f"❌ Error en la sincronización: {e}")

def main():
    # Configurar el trabajo para que se ejecute cada hora
    schedule.every(1).hours.do(job)
    
    print("🔄 Iniciando scheduler...")
    print("ℹ️ La sincronización se ejecutará cada hora")
    print("ℹ️ Presiona Ctrl+C para detener")
    
    # Ejecutar la primera sincronización inmediatamente
    job()
    
    # Mantener el scheduler corriendo
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Esperar 1 minuto antes de la siguiente verificación
        except KeyboardInterrupt:
            print("\n👋 Deteniendo scheduler...")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error en el scheduler: {e}")
            time.sleep(60)  # Esperar antes de reintentar

if __name__ == "__main__":
    main() 