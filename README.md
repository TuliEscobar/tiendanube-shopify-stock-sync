# Sincronizador de Stock Tiendanube-Shopify

Este proyecto sincroniza el stock de productos entre Tiendanube y Shopify, manteniendo Shopify actualizado con los niveles de stock de Tiendanube.

## Características

- Sincronización unidireccional de stock desde Tiendanube hacia Shopify
- Manejo de stock infinito (convierte stock `null` de Tiendanube a 999 en Shopify)
- Soporte para múltiples tiendas Tiendanube
- Programador de tareas para sincronización automática cada hora

## Requisitos

- Python 3.8 o superior
- Credenciales de API de Tiendanube
- Credenciales de API de Shopify

## Instalación

1. Clonar el repositorio:
```bash
git clone [url-del-repositorio]
cd [nombre-del-directorio]
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar el archivo `.env` en la carpeta `src`:
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
   - Obtiene los productos de Tiendanube
   - Si encuentra stock infinito (null), lo convierte a 999
   - Busca el producto correspondiente en Shopify por SKU
   - Actualiza el stock en Shopify

## Notas Importantes

- Los SKUs en Shopify deben seguir el formato: `{tiendanube_product_id}-{tiendanube_variant_id}`
- Se requiere una ubicación en Shopify llamada "Shop location"
- El stock infinito en Tiendanube (null) se convierte a 999 en Shopify 