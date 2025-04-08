# Sincronizador Tiendanube-Shopify

Este proyecto proporciona una herramienta para sincronizar productos entre Tiendanube y Shopify, permitiendo la gestión unificada de inventario y productos entre ambas plataformas.

## Características

- Integración con la API de Tiendanube
- Integración con la API de Shopify
- Sincronización de productos
- Gestión de variantes
- Manejo de categorías
- Operaciones en paralelo para Tiendanube

## Requisitos

- Python 3.8 o superior
- Credenciales de API de Tiendanube
- Credenciales de API de Shopify

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/TuliEscobar/tiendanube-sync.git
cd tiendanube-sync
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar las variables de entorno en un archivo `.env`:
```env
TIENDANUBE_ACCESS_TOKEN=tu_token
TIENDANUBE_STORE_ID=tu_store_id
SHOPIFY_SHOP_URL=tu_tienda.myshopify.com
SHOPIFY_ACCESS_TOKEN=tu_token
```

## Uso

El proyecto proporciona dos clases principales:

### TiendanubeAPI

```python
from src.tiendanube import TiendanubeAPI

# Inicializar cliente
client = TiendanubeAPI(access_token="tu_token", store_id="tu_store_id")

# Obtener productos
products = client.get_products()
```

### ShopifyAPI

```python
from src.shopify import ShopifyAPI

# Inicializar cliente
client = ShopifyAPI(shop_url="tu_tienda.myshopify.com", access_token="tu_token")

# Obtener productos
products = client.get_products()
```

## Estructura del Proyecto

```
.
├── src/
│   ├── tiendanube.py    # Cliente API de Tiendanube
│   └── shopify.py       # Cliente API de Shopify
├── requirements.txt     # Dependencias del proyecto
└── README.md           # Documentación
```

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles. 