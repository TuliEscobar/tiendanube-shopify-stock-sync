import os
import json
import requests
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv
from .store_config import StoreConfig
import time

class TiendanubeAPI:
    def __init__(self, api_url: str = None, token: str = None, user_agent: str = None, store_config: Dict = None):
        """
        Inicializa la API de Tiendanube con credenciales o configuración de tienda
        
        Args:
            api_url (str, optional): URL base de la API. Defaults to None.
            token (str, optional): Token de autenticación. Defaults to None.
            user_agent (str, optional): User agent para las peticiones. Defaults to None.
            store_config (Dict, optional): Configuración completa de la tienda. Defaults to None.
        """
        if store_config:
            self.api_url = str(store_config.get('api_url', '')).rstrip('/')
            self.token = store_config.get('token', '')
            self.user_agent = store_config.get('user_agent', '')
        else:
            self.api_url = api_url.rstrip('/') if api_url else None
            self.token = token
            self.user_agent = user_agent or 'Conexion a Tienda Nube (devs.tiendaonline@gmail.com)'
            
        if not self.api_url or not self.token:
            raise ValueError("Se requiere api_url y token")
            
        # Extraer el store_id de la URL de la API
        try:
            self.store_id = self.api_url.split('/')[-1]
        except:
            raise ValueError(f"No se pudo extraer el store_id de la URL: {self.api_url}")
            
        self.headers = {
            'Authentication': self.token,
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json'
        }
        
        print(f"✅ API de Tiendanube inicializada")
        print(f"🔹 URL Base: {self.api_url}")

    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, 
                     max_retries: int = 3, retry_delay: int = 1) -> requests.Response:
        """
        Realiza una petición HTTP a la API con reintentos
        
        Args:
            method (str): Método HTTP (GET, POST, PUT, DELETE)
            endpoint (str): Endpoint de la API
            params (Dict, optional): Parámetros de query. Defaults to None.
            data (Dict, optional): Datos para POST/PUT. Defaults to None.
            max_retries (int, optional): Número máximo de reintentos. Defaults to 3.
            retry_delay (int, optional): Segundos entre reintentos. Defaults to 1.
            
        Returns:
            requests.Response: Respuesta de la API
            
        Raises:
            Exception: Si la petición falla después de todos los reintentos
        """
        url = f"{self.api_url}/{endpoint}"
        
        for attempt in range(max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=data
                )
                
                # Si es exitoso o es un error que no se debe reintentar
                if response.status_code < 500:
                    return response
                    
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Error en la petición después de {max_retries} intentos: {str(e)}")
                    
            # Esperar antes de reintentar
            time.sleep(retry_delay)
            
        raise Exception(f"Error en la petición después de {max_retries} intentos")
        
    def get_products(self, page: int = 1, per_page: int = 50, params: Dict = None) -> Dict:
        """
        Obtiene la lista de productos
        
        Args:
            page (int, optional): Número de página. Defaults to 1.
            per_page (int, optional): Productos por página. Defaults to 50.
            params (Dict, optional): Parámetros adicionales. Defaults to None.
            
        Returns:
            Dict: Respuesta de la API con los productos
        """
        all_params = {
            'page': page,
            'per_page': per_page
        }
        if params:
            all_params.update(params)
            
        response = self._make_request('GET', 'products', params=all_params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error al obtener productos: {response.text}")
            
    def get_product(self, product_id: Union[str, int]) -> Dict:
        """
        Obtiene los detalles de un producto específico
        
        Args:
            product_id (Union[str, int]): ID del producto
            
        Returns:
            Dict: Detalles del producto
        """
        response = self._make_request('GET', f'products/{product_id}')
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error al obtener el producto {product_id}: {response.text}")
            
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