# Sincronizador Tiendanube-Shopify

Este proyecto proporciona una herramienta para sincronizar productos entre Tiendanube y Shopify, permitiendo la gestión unificada de inventario y productos entre ambas plataformas.

## Características

- Integración con múltiples tiendas de Tiendanube
- Integración con la API de Shopify
- Sincronización bidireccional de productos
- Gestión completa de variantes y opciones de productos
- Sincronización de imágenes de productos
- Manejo de inventario
- Soporte para múltiples tiendas en paralelo

## Requisitos

- Python 3.8 o superior
- Credenciales de API de Tiendanube para cada tienda
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

3. Configurar las variables de entorno en `src/.env`:
```env
# Configuración de Tiendanube
TIENDANUBE_CREDENTIALS=[
    {
        "base_url": "https://api.tiendanube.com/v1/store_id_1",
        "headers": {
            "Authentication": "bearer your_token_1",
            "User-Agent": "your_app_name"
        }
    }
]

# Configuración de Shopify
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_access_token
```

## Uso

### Sincronización de Productos

```python
from src.tiendanube import TiendanubeAPI
from src.shopify import ShopifyAPI

# Inicializar clientes
tiendanube = TiendanubeAPI(store_number=1)
shopify = ShopifyAPI()

# Obtener productos de Tiendanube
products = tiendanube.get_products(include_variants=True)

# Sincronizar con Shopify
for product in products:
    shopify.create_product(product)
```

### TiendanubeAPI

```python
from src.tiendanube import TiendanubeAPI

# Inicializar cliente
client = TiendanubeAPI(store_number=1)

# Obtener productos con variantes
products = client.get_products(include_variants=True)

# Obtener un producto específico
product = client.get_product(product_id=123, include_variants=True)
```

### ShopifyAPI

```python
from src.shopify import ShopifyAPI

# Inicializar cliente
client = ShopifyAPI()

# Crear producto con variantes
response = client.create_product({
    "name": {"es": "Nuevo Producto"},
    "variants": [
        {
            "price": "100.00",
            "stock": 10,
            "values": [{"es": "Rojo"}]
        }
    ],
    "attributes": [{"es": "Color"}]
})
```

## Estructura del Proyecto

```
.
├── src/
│   ├── tiendanube.py      # Cliente API de Tiendanube
│   ├── shopify.py         # Cliente API de Shopify
│   ├── sync_products.py   # Módulo de sincronización
│   └── .env              # Configuración de credenciales
├── test_products.py       # Script de prueba para productos
├── test_sync_products.py  # Script de prueba para sincronización
├── test_shopify.py       # Script de prueba para Shopify
├── requirements.txt      # Dependencias del proyecto
└── README.md            # Documentación
```

## Scripts de Utilidad

### test_products.py
Muestra todos los productos y sus variantes de las tiendas configuradas:
```bash
python test_products.py
```

### test_sync_products.py
Sincroniza productos de Tiendanube a Shopify:
```bash
python test_sync_products.py
```

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles. 