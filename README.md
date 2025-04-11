# 🔄 Sincronización Tiendanube-Shopify

Sistema automatizado para sincronizar productos e inventario entre Tiendanube y Shopify.

## 🚀 Características

- **Sincronización de Productos**
  - Crea y actualiza productos de Tiendanube en Shopify
  - Sincroniza todas las variantes y sus atributos
  - Mantiene los precios actualizados
  - Transfiere imágenes y descripciones completas
  - Genera SKUs únicos basados en IDs de producto y variante

- **Sincronización de Inventario**
  - Actualiza el stock en Shopify basado en el inventario de Tiendanube
  - Usa SKUs compuestos (ID_PRODUCTO-ID_VARIANTE) para mapeo preciso
  - Mantiene el stock en la ubicación "Shop location" de Shopify
  - Evita duplicados y solo actualiza cuando hay cambios reales

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
TIENDANUBE_CREDENTIALS='[
    {
        "base_url": "https://api.tiendanube.com/v1/TU_ID_TIENDA",
        "headers": {
            "Authentication": "bearer TU_TOKEN",
            "User-Agent": "TU_APP_NAME"
        }
    }
]'

# Shopify
SHOPIFY_SHOP_URL="tu-tienda.myshopify.com"
SHOPIFY_ACCESS_TOKEN="tu_access_token"
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
- Mensajes promocionales enviados
- Resumen final de la sincronización


## 🔍 Logs de Ejemplo

```
🔄 Iniciando sincronización de productos...
✅ Se encontraron 150 productos en Tiendanube
✅ Se encontraron 145 productos en Shopify

📦 Procesando producto: "Notebook HP 15"
✅ Producto creado/actualizado en Shopify
✅ 3 variantes sincronizadas
✅ 5 imágenes transferidas

📦 Procesando producto ID: 252417560, variante ID: 1114904464
✅ SKU encontrado en Shopify: 252417560-1114904464
Stock actual: 5
Nuevo stock: 8
✅ Inventario actualizado correctamente

📊 Resumen de sincronización:
- Productos creados: 5
- Productos actualizados: 140
- Variantes sincronizadas: 450
- Imágenes transferidas: 300
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue primero para discutir los cambios que te gustaría hacer.

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles. 