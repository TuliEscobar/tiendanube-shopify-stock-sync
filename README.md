# Sincronizador de Stock Tiendanube-Shopify

Este proyecto sincroniza el stock de productos entre Tiendanube y Shopify, manteniendo Shopify actualizado con los niveles de stock de Tiendanube.

## Características

- Sincronización unidireccional de stock desde Tiendanube hacia Shopify
- Sincronización optimizada: solo procesa productos modificados en los últimos 15 minutos
- Manejo de stock infinito (convierte stock `null` de Tiendanube a 999 en Shopify)
- Soporte para múltiples tiendas Tiendanube
- Programador de tareas para sincronización automática cada hora
- Manejo individual de variantes y sus SKUs
- Sistema robusto de manejo de errores y estadísticas por tienda

## Requisitos

- Python 3.8 o superior
- Credenciales de API de Tiendanube
- Credenciales de API de Shopify

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/TuliEscobar/tiendanube-shopify-stock-sync.git
cd tiendanube-shopify-stock-sync
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar el archivo `.env` en la raíz del proyecto:
```env
# Configuración de Shopify
SHOPIFY_STORE_URL=https://tu-tienda.myshopify.com/admin/api/2023-01
SHOPIFY_ACCESS_TOKEN=tu_token_de_acceso

# Configuración de Tiendanube (formato JSON)
TIENDANUBE_CREDENTIALS=[
  {
    "base_url": "https://api.tiendanube.com/v1/123456",
    "headers": {
      "Authentication": "bearer tu-token-de-tiendanube",
      "User-Agent": "Tu Aplicación (email@ejemplo.com)"
    }
  },
  {
    "base_url": "https://api.tiendanube.com/v1/789012",
    "headers": {
      "Authentication": "bearer otro-token-de-tiendanube",
      "User-Agent": "Tu Aplicación (email@ejemplo.com)"
    }
  }
]
```

## Uso

### Sincronización Manual

Para ejecutar una sincronización manual:
```bash
python src/sync_products.py
```

### Sincronización Automática

Para iniciar el programador de tareas que ejecuta la sincronización cada hora:
```bash
python scheduler.py
```

## Estructura del Proyecto

- `src/sync_products.py`: Script principal de sincronización
- `src/store_config.py`: Manejo de configuración de tiendas
- `src/shopify.py`: Cliente API de Shopify
- `src/tiendanube.py`: Cliente API de Tiendanube
- `scheduler.py`: Programador de tareas

## Funcionamiento

1. El script carga la configuración de las tiendas desde el archivo `.env`
2. Para cada tienda configurada:
   - Obtiene los productos modificados en los últimos 15 minutos
   - Filtra productos publicados con stock mínimo de 1
   - Procesa cada producto y sus variantes:
     - Si una variante tiene stock infinito (null), lo establece en 999
     - Asigna el ID de la variante como SKU
   - Busca el producto correspondiente en Shopify usando el SKU
   - Actualiza el stock en Shopify manteniendo la relación 1:1 entre variantes
   - Mantiene estadísticas individuales por tienda

## Notas Importantes

- Los SKUs en Shopify se asignan automáticamente:
  - Para productos con variantes: el SKU es el ID de la variante de Tiendanube
  - Para productos sin variantes: el SKU es el ID del producto de Tiendanube
- Se requiere una ubicación en Shopify llamada "Shop location"
- El stock infinito en Tiendanube (null) se convierte a 999 en Shopify
- Cada tienda mantiene sus propias estadísticas y registro de errores
- El sistema es tolerante a fallos: si una tienda falla, continúa con las demás
- Solo se procesan productos actualizados en los últimos 15 minutos para optimizar recursos

## Logs y Monitoreo

El sistema proporciona información detallada durante la sincronización:
- Número de productos encontrados por tienda
- Timestamp de la última actualización considerada
- Estado de sincronización de cada producto
- Conversiones de stock infinito
- Estadísticas globales y por tienda
- Errores detallados en caso de fallos 