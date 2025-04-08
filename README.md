# Sincronizador Tiendanube-Shopify

Este proyecto proporciona una herramienta para sincronizar productos entre Tiendanube y Shopify, permitiendo la gestión unificada de inventario y productos entre ambas plataformas.

## Características

- Integración con múltiples tiendas de Tiendanube
- Integración con la API de Shopify
- Sincronización de productos
- Gestión de variantes
- Manejo de categorías
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

3. Configurar las variables de entorno en un archivo `.env`:
```env
# Configuración de Tiendanube
TIENDANUBE_CREDENTIALS=[
    {
        "base_url": "https://api.tiendanube.com/v1/store_id_1",
        "headers": {
            "Authentication": "bearer your_token_1",
            "User-Agent": "your_app_name"
        }
    },
    {
        "base_url": "https://api.tiendanube.com/v1/store_id_2",
        "headers": {
            "Authentication": "bearer your_token_2",
            "User-Agent": ""
        }
    }
]
```

## Uso

### TiendanubeAPI

```python
from src.tiendanube import TiendanubeAPI

# Inicializar cliente para una tienda específica (1-4)
client = TiendanubeAPI(store_number=1)

# Obtener productos con variantes
products = client.get_products(include_variants=True)

# Obtener un producto específico
product = client.get_product(product_id=123, include_variants=True)

# Crear un nuevo producto
new_product = client.create_product({
    "name": {"es": "Nuevo Producto"},
    "price": 100.00,
    "stock": 10
})

# Actualizar un producto
updated_product = client.update_product(123, {
    "price": 150.00,
    "stock": 5
})

# Eliminar un producto
client.delete_product(123)
```

## Estructura del Proyecto

```
.
├── src/
│   ├── tiendanube.py    # Cliente API de Tiendanube
│   └── shopify.py       # Cliente API de Shopify
├── test_products.py     # Script de prueba para productos
├── Utils.py            # Utilidades generales
├── requirements.txt    # Dependencias del proyecto
└── README.md          # Documentación
```

## Scripts de Utilidad

### test_products.py

Este script permite obtener y mostrar todos los productos de todas las tiendas configuradas:

```python
python test_products.py
```

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles. 