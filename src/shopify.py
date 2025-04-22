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
        
        # Obtener y almacenar la ubicación principal
        self.shop_location_id = self._get_shop_location_id()

    def _get_shop_location_id(self) -> str:
        """
        Obtiene el ID de la ubicación principal de la tienda
        
        Returns:
            str: ID de la ubicación principal
        """
        try:
            response = requests.get(
                f"{self.api_url}/locations.json",
                headers=self.headers
            )
            response.raise_for_status()
            
            locations = response.json().get('locations', [])
            main_location = next(
                (loc for loc in locations if loc['name'] == 'Shop location'),
                None
            )
            
            if not main_location:
                raise ValueError("No se encontró la ubicación 'Shop location'")
                
            return main_location['id']
            
        except Exception as e:
            print(f"Error al obtener ubicación principal: {e}")
            raise

    def find_variant_by_sku(self, sku: str) -> Dict:
        """
        Busca una variante por su SKU
        
        Args:
            sku (str): SKU de la variante a buscar
            
        Returns:
            Dict: Datos de la variante encontrada o None si no existe
        """
        try:
            # Buscar la variante usando la API de variantes
            response = requests.get(
                f"{self.api_url}/variants.json",
                headers=self.headers,
                params={'sku': sku}
            )
            response.raise_for_status()
            
            variants = response.json().get('variants', [])
            if variants:
                return variants[0]
            
            return None
            
        except Exception as e:
            print(f"Error al buscar variante por SKU {sku}: {e}")
            return None

    def get_variant_stock(self, variant_id: str) -> int:
        """
        Obtiene el stock actual de una variante
        
        Args:
            variant_id (str): ID de la variante
            
        Returns:
            int: Cantidad en stock
        """
        try:
            # Primero obtener el inventory_item_id de la variante
            response = requests.get(
                f"{self.api_url}/variants/{variant_id}.json",
                headers=self.headers
            )
            response.raise_for_status()
            
            variant = response.json().get('variant', {})
            inventory_item_id = variant.get('inventory_item_id')
            
            if not inventory_item_id:
                return 0
            
            # Obtener el nivel de inventario
            response = requests.get(
                f"{self.api_url}/inventory_levels.json",
                headers=self.headers,
                params={
                    'inventory_item_ids': inventory_item_id,
                    'location_ids': self.shop_location_id
                }
            )
            response.raise_for_status()
            
            levels = response.json().get('inventory_levels', [])
            if levels:
                return levels[0].get('available', 0)
            
            return 0
            
        except Exception as e:
            print(f"Error al obtener stock de la variante {variant_id}: {e}")
            return 0

    def update_variant_stock(self, variant_id: str, new_quantity: int) -> bool:
        """
        Actualiza el stock de una variante
        
        Args:
            variant_id (str): ID de la variante
            new_quantity (int): Nueva cantidad de stock
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            print(f"\n🔄 Actualizando stock de variante {variant_id} a {new_quantity}")
            
            # Primero obtener el inventory_item_id de la variante
            response = requests.get(
                f"{self.api_url}/variants/{variant_id}.json",
                headers=self.headers
            )
            response.raise_for_status()
            
            variant = response.json().get('variant', {})
            inventory_item_id = variant.get('inventory_item_id')
            
            if not inventory_item_id:
                print(f"❌ No se encontró inventory_item_id para la variante {variant_id}")
                return False
            
            print(f"✅ Encontrado inventory_item_id: {inventory_item_id}")
            
            # Actualizar el nivel de inventario
            update_url = f"{self.api_url}/inventory_levels/set.json"
            update_data = {
                'inventory_item_id': inventory_item_id,
                'location_id': self.shop_location_id,
                'available': int(new_quantity)
            }
            
            print(f"📤 Enviando actualización a Shopify:")
            print(f"   URL: {update_url}")
            print(f"   Datos: {json.dumps(update_data, indent=2)}")
            
            response = requests.post(
                update_url,
                headers=self.headers,
                json=update_data
            )
            
            if response.status_code != 200:
                print(f"❌ Error al actualizar stock. Código: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
                
            result = response.json()
            print(f"✅ Stock actualizado correctamente")
            print(f"   Respuesta: {json.dumps(result, indent=2)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error al actualizar stock de la variante {variant_id}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Respuesta del servidor: {e.response.text}")
            return False

    def create_product(self, tiendanube_product: Dict) -> Dict:
        """
        Crea un producto en Shopify basado en los datos de un producto de Tiendanube
        
        Args:
            tiendanube_product (Dict): Producto de Tiendanube con su información y variantes
            
        Returns:
            Dict: Producto creado en Shopify
        """
        # Obtener el ID de la tienda de Tiendanube de la URL base
        tiendanube_store_id = tiendanube_product.get('store_id', 'unknown')
        tiendanube_product_id = tiendanube_product.get('id')
        
        # Convertir el formato de Tiendanube al formato de Shopify
        shopify_product = {
            "product": {
                "title": tiendanube_product.get('name', {}).get('es', 'Sin nombre'),
                "body_html": tiendanube_product.get('description', {}).get('es', ''),
                "product_type": tiendanube_product.get('category', ''),
                "status": "active" if tiendanube_product.get('published') else "draft",
                "variants": [],
                "options": [],
                "images": [],
                "tags": f"{tiendanube_store_id}"
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
                # Usar el ID de la variante de Tiendanube como SKU
                variant_id = variant.get('id')
                sku = f"{tiendanube_product_id}-{variant_id}"
                
                shopify_variant = {
                    "price": str(variant.get('price', 0)),
                    "sku": sku,
                    "inventory_quantity": variant.get('stock', 0),
                    "inventory_management": "shopify",
                    "inventory_policy": "deny",
                    "barcode": variant.get('barcode', '')  # Mantener el código de barras si existe
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
            # Si no hay variantes, usar el ID del producto como SKU
            sku = str(tiendanube_product_id)
            
            shopify_product["product"]["variants"].append({
                "price": str(tiendanube_product.get('price', 0)),
                "sku": sku,
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

    def sync_products_from_tiendanube(self, tiendanube_product: Dict) -> bool:
        """
        Sincroniza un producto desde Tiendanube a Shopify, actualizando stock si existe
        o creando el producto si no existe
        
        Args:
            tiendanube_product (Dict): Producto de Tiendanube con su información y variantes
            
        Returns:
            bool: True si se actualizó/creó correctamente
        """
        try:
            tiendanube_id = str(tiendanube_product.get('id'))
            print(f"\n🔄 Sincronizando producto de Tiendanube ID: {tiendanube_id}")
            
            # Verificar si el producto existe buscando por variantes
            product_exists = False
            variants = tiendanube_product.get('variants', [])
            
            if variants:
                for variant in variants:
                    variant_id = str(variant.get('id'))
                    sku = f"{tiendanube_id}-{variant_id}"
                    print(f"\n🔍 Buscando variante con SKU: {sku}")
                    
                    shopify_variant = self.find_variant_by_sku(sku)
                    
                    if shopify_variant:
                        product_exists = True
                        print(f"✅ Variante encontrada en Shopify - ID: {shopify_variant['id']}")
                        
                        current_stock = self.get_variant_stock(shopify_variant['id'])
                        new_stock = variant.get('stock', 0)
                        
                        print(f"📊 Stock actual en Shopify: {current_stock}")
                        print(f"📊 Nuevo stock de Tiendanube: {new_stock}")
                        
                        # Forzar actualización de stock
                        if self.update_variant_stock(shopify_variant['id'], new_stock):
                            print(f"✅ Stock actualizado correctamente")
                        else:
                            print(f"❌ Error al actualizar stock")
                            return False
                    else:
                        print(f"❌ Variante no encontrada en Shopify")
            else:
                # Producto simple
                sku = tiendanube_id
                print(f"\n🔍 Buscando producto simple con SKU: {sku}")
                
                shopify_variant = self.find_variant_by_sku(sku)
                
                if shopify_variant:
                    product_exists = True
                    print(f"✅ Producto encontrado en Shopify - ID: {shopify_variant['id']}")
                    
                    current_stock = self.get_variant_stock(shopify_variant['id'])
                    new_stock = tiendanube_product.get('stock', 0)
                    
                    print(f"📊 Stock actual en Shopify: {current_stock}")
                    print(f"📊 Nuevo stock de Tiendanube: {new_stock}")
                    
                    # Forzar actualización de stock
                    if self.update_variant_stock(shopify_variant['id'], new_stock):
                        print(f"✅ Stock actualizado correctamente")
                    else:
                        print(f"❌ Error al actualizar stock")
                        return False
                else:
                    print(f"❌ Producto no encontrado en Shopify")
            
            # Si el producto no existe, crearlo
            if not product_exists:
                print(f"🆕 Creando nuevo producto en Shopify")
                shopify_product = self.create_product(tiendanube_product)
                print(f"✅ Producto creado: {shopify_product.get('product', {}).get('title')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error al sincronizar producto {tiendanube_product.get('id')}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Respuesta del servidor: {e.response.text}")
            return False

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