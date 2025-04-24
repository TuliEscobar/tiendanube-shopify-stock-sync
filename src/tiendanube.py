import os
import json
import requests
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv
from .store_config import StoreConfig
import time

class TiendanubeAPI:
    def __init__(self, api_url: str = None, token: str = None, user_agent: str = None):
        """
        Inicializa la API de Tiendanube
        
        Args:
            api_url (str, optional): URL base de la API. Si no se proporciona, se usa TIENDANUBE_STORE_ID
            token (str, optional): Token de acceso. Si no se proporciona, se usa TIENDANUBE_ACCESS_TOKEN
            user_agent (str, optional): User Agent para las peticiones
        """
        load_dotenv()
        
        # Si no se proporcionan parámetros, usar variables de entorno
        if not api_url:
            store_id = os.getenv('TIENDANUBE_STORE_ID')
            if not store_id:
                raise ValueError("TIENDANUBE_STORE_ID no está configurado en .env")
            api_url = f"https://api.tiendanube.com/v1/{store_id}"
            
        if not token:
            token = os.getenv('TIENDANUBE_ACCESS_TOKEN')
            if not token:
                raise ValueError("TIENDANUBE_ACCESS_TOKEN no está configurado en .env")
                
        if not user_agent:
            user_agent = 'Stock Sync App (tuli.escobar@gmail.com)'
            
        # Asegurar que el token tenga el prefijo "bearer"
        if not token.lower().startswith('bearer '):
            token = f"bearer {token}"
            
        self.api_url = api_url
        self.headers = {
            'Authentication': token,
            'Content-Type': 'application/json',
            'User-Agent': user_agent
        }
        
        print("✅ API de Tiendanube inicializada")
        print(f"🔹 URL: {self.api_url}")
        print(f"🔹 Token: {token[:20]}...")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Realiza una petición a la API de Tiendanube
        
        Args:
            method (str): Método HTTP
            endpoint (str): Endpoint de la API
            **kwargs: Argumentos adicionales para la petición
            
        Returns:
            requests.Response: Respuesta de la API
        """
        url = f"{self.api_url}/{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        
        if response.status_code not in [200, 201]:
            print(f"❌ Error en petición a Tiendanube: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            raise Exception(f"Error en petición a Tiendanube: {response.status_code}")
            
        return response

    def get_products(self) -> List[Dict]:
        """
        Obtiene todos los productos de la tienda
        
        Returns:
            List[Dict]: Lista de productos
        """
        response = self._make_request('GET', 'products')
        products = response.json()
        
        # Asegurar que los SKUs estén configurados correctamente
        for product in products:
            variants = product.get('variants', [])
            if variants:
                # Producto con variantes - usar ID de variante como SKU
                for variant in variants:
                    variant['sku'] = str(variant['id'])
            else:
                # Producto sin variantes - usar ID de producto como SKU
                product['sku'] = str(product['id'])
        
        return products

    def get_product(self, product_id: str) -> Optional[Dict]:
        """
        Obtiene un producto específico
        
        Args:
            product_id (str): ID del producto
            
        Returns:
            Optional[Dict]: Producto encontrado o None
        """
        try:
            response = self._make_request('GET', f'products/{product_id}')
            product = response.json()
            
            # Configurar SKUs
            variants = product.get('variants', [])
            if variants:
                for variant in variants:
                    variant['sku'] = str(variant['id'])
            else:
                product['sku'] = str(product['id'])
                
            return product
        except Exception as e:
            print(f"❌ Error obteniendo producto {product_id}: {e}")
            return None
            
    def create_product(self, product_data: Dict) -> Dict:
        """
        Crea un nuevo producto
        
        Args:
            product_data (Dict): Datos del producto a crear
            
        Returns:
            Dict: Producto creado
        """
        response = self._make_request('POST', 'products', data=product_data)
        
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Error al crear el producto: {response.text}")
            
    def update_product(self, product_id: Union[str, int], product_data: Dict) -> Dict:
        """
        Actualiza un producto existente
        
        Args:
            product_id (Union[str, int]): ID del producto
            product_data (Dict): Datos actualizados del producto
            
        Returns:
            Dict: Producto actualizado
        """
        response = self._make_request('PUT', f'products/{product_id}', data=product_data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error al actualizar el producto {product_id}: {response.text}")
            
    def delete_product(self, product_id: Union[str, int]) -> bool:
        """
        Elimina un producto
        
        Args:
            product_id (Union[str, int]): ID del producto
            
        Returns:
            bool: True si se eliminó correctamente
        """
        response = self._make_request('DELETE', f'products/{product_id}')
        
        if response.status_code == 200:
            return True
        else:
            raise Exception(f"Error al eliminar el producto {product_id}: {response.text}")
            
    def get_variants(self, product_id: Union[str, int]) -> List[Dict]:
        """
        Obtiene las variantes de un producto
        
        Args:
            product_id (Union[str, int]): ID del producto
            
        Returns:
            List[Dict]: Lista de variantes
        """
        response = self._make_request('GET', f'products/{product_id}/variants')
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error al obtener variantes del producto {product_id}: {response.text}")
            
    def create_variant(self, product_id: Union[str, int], variant_data: Dict) -> Dict:
        """
        Crea una nueva variante para un producto
        
        Args:
            product_id (Union[str, int]): ID del producto
            variant_data (Dict): Datos de la variante
            
        Returns:
            Dict: Variante creada
        """
        response = self._make_request('POST', f'products/{product_id}/variants', data=variant_data)
        
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Error al crear variante para el producto {product_id}: {response.text}")
            
    def update_variant(self, product_id: Union[str, int], variant_id: Union[str, int], 
                      variant_data: Dict) -> Dict:
        """
        Actualiza una variante existente
        
        Args:
            product_id (Union[str, int]): ID del producto
            variant_id (Union[str, int]): ID de la variante
            variant_data (Dict): Datos actualizados de la variante
            
        Returns:
            Dict: Variante actualizada
        """
        response = self._make_request(
            'PUT', 
            f'products/{product_id}/variants/{variant_id}', 
            data=variant_data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Error al actualizar variante {variant_id} del producto {product_id}: {response.text}"
            )
            
    def delete_variant(self, product_id: Union[str, int], variant_id: Union[str, int]) -> bool:
        """
        Elimina una variante
        
        Args:
            product_id (Union[str, int]): ID del producto
            variant_id (Union[str, int]): ID de la variante
            
        Returns:
            bool: True si se eliminó correctamente
        """
        response = self._make_request('DELETE', f'products/{product_id}/variants/{variant_id}')
        
        if response.status_code == 200:
            return True
        else:
            raise Exception(
                f"Error al eliminar variante {variant_id} del producto {product_id}: {response.text}"
            )
            
    def update_variant_stock(self, product_id: Union[str, int], variant_id: Union[str, int], new_stock: int) -> bool:
        """
        Actualiza el stock de una variante
        
        Args:
            product_id (Union[str, int]): ID del producto
            variant_id (Union[str, int]): ID de la variante
            new_stock (int): Nueva cantidad de stock
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            print(f"\n🔄 Actualizando stock de variante {variant_id} a {new_stock}")
            
            # Preparar datos de actualización
            update_data = {'stock': new_stock}
            
            # Realizar la actualización
            response = self._make_request(
                'PUT',
                f'products/{product_id}/variants/{variant_id}',
                data=update_data
            )
            
            if response.status_code == 200:
                print(f"✅ Stock actualizado correctamente")
                return True
            else:
                print(f"❌ Error al actualizar stock. Código: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error al actualizar stock de la variante {variant_id}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Respuesta del servidor: {e.response.text}")
            return False 