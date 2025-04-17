# 🔄 Sincronización Tiendanube-Shopify

Sistema automatizado para sincronizar productos e inventario entre Tiendanube y Shopify.

## 🚀 Características

- **Sincronización de Productos**
  - Crea y actualiza productos de Tiendanube en Shopify
  - Sincroniza todas las variantes y sus atributos
  - Mantiene los precios actualizados
  - Transfiere imágenes y descripciones completas
  - Genera SKUs únicos basados en IDs de producto y variante

- **Sistema de Caché de Stock**
  - Archivos `stock_cache_{store_id}.json` para cada tienda
  - Evita actualizaciones innecesarias comparando con el último estado conocido
  - Actualización inteligente basada en cambios reales de stock
  - Ignorados por git para evitar conflictos entre diferentes entornos
  - Regeneración automática si el archivo está corrupto o no existe

- **Sincronización de Inventario**
  - Actualiza el stock en Shopify basado en el inventario de Tiendanube
  - Usa SKUs compuestos (ID_PRODUCTO-ID_VARIANTE) para mapeo preciso
  - Mantiene el stock en la ubicación "Shop location" de Shopify
  - Evita duplicados y solo actualiza cuando hay cambios reales
  - Crea automáticamente nuevas variantes si se detectan en Tiendanube
  - Sincroniza el stock inicial al crear nuevas variantes
  - Control de rate limits para evitar sobrecarga de las APIs

- **Gestión de Productos**
  - Soporta productos con y sin variantes
  - Mantiene la integridad de los datos entre plataformas
  - Logging detallado del proceso de sincronización
  - Manejo de categorías y colecciones
  - Sincronización de metadatos y tags


## 🛠️ Configuración

1. Crea un archivo `.env` con las siguientes variables:

```env
# Tiendanube
# Puedes configurar múltiples tiendas en el array de TIENDANUBE_CREDENTIALS
TIENDANUBE_CREDENTIALS='[
    {
        "base_url": "https://api.tiendanube.com/v1/5757772",
        "headers": {
            "Authentication": "bearer tu_token_aqui",
            "User-Agent": "Mi App (tu@email.com)"
        }
    },
    {
        "base_url": "https://api.tiendanube.com/v1/otra_tienda",
        "headers": {
            "Authentication": "bearer otro_token",
            "User-Agent": "Mi App (tu@email.com)"
        }
    }
]'

# Shopify
SHOPIFY_SHOP_URL="tu-tienda.myshopify.com"
SHOPIFY_ACCESS_TOKEN="shpat_tu_token_aqui"

# Configuración opcional
DEBUG=True  # Habilita logs adicionales
RATE_LIMIT_DELAY=0.5  # Delay entre llamadas API en segundos
```

## 📦 Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/tu-usuario/sync_tiendanube_shopify.git
cd sync_tiendanube_shopify
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## 🚀 Uso

Para ejecutar la sincronización de productos (creación y actualización):
```bash
python src/sync_products.py
```

Para ejecutar la sincronización de inventario:
```bash
python src/sync_inventory.py
```

## 📊 Monitoreo

El sistema proporciona logs detallados que incluyen:
- Productos encontrados en cada plataforma
- Productos creados o actualizados
- SKUs procesados y resultados
- Cambios de stock realizados
- Creación de nuevas variantes
- Resumen por tienda y global
- Control de rate limits y errores

## 🔍 Logs de Ejemplo

```
🔄 Procesando 2 tiendas...

📦 Procesando tienda 1/2
🔹 URL: https://api.tiendanube.com/v1/5757772
✅ Inicialización completada

🔄 Iniciando sincronización de inventario...
✅ Se encontraron 150 productos en Tiendanube
✅ Se encontraron 145 productos en Shopify
✅ Se encontraron 2 ubicaciones en Shopify

📦 Procesando producto: "Notebook HP 15"
ℹ️ Stock sin cambios para variante ID: 7379351470214-41741744504966 (Stock: 623)
✅ Nueva variante creada - SKU: 252417560-1114904464
✅ Stock actualizado - Producto ID: 7379351470214-41741744504966 | 0 → 8

📊 Resumen de la tienda:
- Productos actualizados: 45
- Productos sin cambios: 100
- Productos no encontrados: 5
- Nuevas variantes creadas: 3

🎉 Proceso completado para todas las tiendas!
📊 Resumen Global:
- Total productos actualizados: 85
- Total productos sin cambios: 200
- Total productos no encontrados: 15
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue primero para discutir los cambios que te gustaría hacer.

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles. 