import os
import requests
import json
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

class ShopifyAPI:
    def __init__(self, shop_url=None, access_token=None):
        """
        Inicializa el cliente de Shopify usando las credenciales del .env o parámetros
        """
        self.shop_url = shop_url or os.getenv('SHOPIFY_SHOP_URL')
        self.access_token = access_token or os.getenv('SHOPIFY_ACCESS_TOKEN')
        
        if not self.shop_url or not self.access_token:
            raise ValueError("SHOPIFY_SHOP_URL y SHOPIFY_ACCESS_TOKEN son requeridos en el archivo .env")
        
        # Asegurarse de que la URL termine en .myshopify.com
        if not self.shop_url.endswith('.myshopify.com'):
            self.shop_url = f"{self.shop_url}.myshopify.com"
            
        self.api_url = f"https://{self.shop_url}/admin/api/2024-01"
        self.headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }

    def create_product(self, tiendanube_product: Dict) -> Dict:
        """
        Crea un producto en Shopify basado en los datos de un producto de Tiendanube
        
        Args:
            tiendanube_product (Dict): Producto de Tiendanube con su información y variantes
            
        Returns:
            Dict: Producto creado en Shopify
        """
        # Convertir el formato de Tiendanube al formato de Shopify
        shopify_product = {
            "product": {
                "title": tiendanube_product.get('name', {}).get('es', 'Sin nombre'),
                "body_html": tiendanube_product.get('description', {}).get('es', ''),
                "vendor": "Tiendanube Import",
                "product_type": tiendanube_product.get('category', ''),
                "status": "active" if tiendanube_product.get('published') else "draft",
                "variants": [],
                "options": [],
                "images": []
            }
        }
        
        # Procesar variantes y opciones
        variants = tiendanube_product.get('variants', [])
        attributes = tiendanube_product.get('attributes', [])
        
        if variants:
            # Crear las opciones del producto basadas en los atributos
            for i, attr in enumerate(attributes, 1):
                option_name = attr.get('es', f'Opción {i}')
                if option_name:  # Solo agregar si el nombre no está vacío
                    # Recolectar valores únicos para esta opción
                    values = set()
                    for variant in variants:
                        if len(variant.get('values', [])) >= i:
                            value = variant['values'][i-1].get('es', '')
                            if value:
                                values.add(value)
                    
                    if values:  # Solo agregar la opción si tiene valores
                        shopify_product["product"]["options"].append({
                            "name": option_name,
                            "position": i,
                            "values": list(values)
                        })
            
            # Crear las variantes con sus opciones
            for variant in variants:
                shopify_variant = {
                    "price": str(variant.get('price', 0)),
                    "sku": variant.get('sku', ''),
                    "inventory_quantity": variant.get('stock', 0),
                    "inventory_management": "shopify",
                    "inventory_policy": "deny"
                }
                
                # Agregar los valores de las opciones a la variante
                for i, value in enumerate(variant.get('values', []), 1):
                    if i <= len(attributes):  # Solo procesar si hay un atributo correspondiente
                        option_value = value.get('es', '')
                        if option_value:  # Solo agregar si el valor no está vacío
                            option_key = f"option{i}"
                            shopify_variant[option_key] = option_value
                
                shopify_product["product"]["variants"].append(shopify_variant)
        else:
            # Si no hay variantes, crear una variante por defecto
            shopify_product["product"]["variants"].append({
                "price": str(tiendanube_product.get('price', 0)),
                "sku": tiendanube_product.get('sku', ''),
                "inventory_quantity": tiendanube_product.get('stock', 0),
                "inventory_management": "shopify",
                "inventory_policy": "deny"
            })
        
        # Procesar imágenes
        images = tiendanube_product.get('images', [])
        for image in images:
            shopify_product["product"]["images"].append({
                "src": image.get('src', '')
            })
        
        try:
            response = requests.post(
                f"{self.api_url}/products.json",
                headers=self.headers,
                json=shopify_product
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al crear producto en Shopify: {e}")
            if hasattr(e.response, 'text'):
                print(f"Respuesta del servidor: {e.response.text}")
            print(f"URL: {self.api_url}/products.json")
            print(f"Producto: {json.dumps(shopify_product, indent=2)}")
            raise

    def sync_products_from_tiendanube(self, tiendanube_products: List[Dict]) -> List[Dict]:
        """
        Sincroniza una lista de productos desde Tiendanube a Shopify
        
        Args:
            tiendanube_products (List[Dict]): Lista de productos de Tiendanube
            
        Returns:
            List[Dict]: Lista de productos creados en Shopify
        """
        created_products = []
        
        for product in tiendanube_products:
            try:
                shopify_product = self.create_product(product)
                created_products.append(shopify_product)
                print(f"Producto creado en Shopify: {shopify_product.get('product', {}).get('title')}")
            except Exception as e:
                print(f"Error al sincronizar producto {product.get('id')}: {e}")
                continue
        
        return created_products

    def get_products(self, limit=50) -> List[Dict]:
        """
        Obtiene la lista de productos de Shopify
        
        Args:
            limit (int): Número máximo de productos a obtener
            
        Returns:
            List[Dict]: Lista de productos
        """
        try:
            url = f"{self.api_url}/products.json"
            print(f"\nRealizando petición a Shopify:")
            print(f"URL: {url}")
            print(f"Headers: {self.headers}")
            
            response = requests.get(
                url,
                headers=self.headers,
                params={'limit': limit}
            )
            
            if response.status_code != 200:
                print(f"\nRespuesta de error de Shopify:")
                print(f"Status Code: {response.status_code}")
                print(f"Response Headers: {dict(response.headers)}")
                print(f"Response Body: {response.text}")
            
            response.raise_for_status()
            return response.json().get('products', [])
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener productos de Shopify: {e}")
            raise 