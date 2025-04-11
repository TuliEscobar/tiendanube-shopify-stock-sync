import os
import json
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

class TiendanubeAPI:
    def __init__(self, credentials: Dict = None):
        # Cargar variables de entorno
        load_dotenv()
        
        if credentials is None:
            # Si no se proporcionan credenciales, usar la primera configuración del .env
            tiendanube_credentials = json.loads(os.getenv('TIENDANUBE_CREDENTIALS', '[]').strip("'"))
            if not tiendanube_credentials:
                raise Exception("No se encontraron credenciales de Tiendanube")
            credentials = tiendanube_credentials[0]
        
        self.base_url = credentials['base_url']
        self.headers = credentials['headers']
        
        print(f"✅ API de Tiendanube inicializada")
        print(f"🔹 URL Base: {self.base_url}")

    def get_products(self, page: int = 1, per_page: int = 50, include_variants: bool = True) -> List[Dict]:
        """
        Obtiene la lista de productos de la tienda.
        
        Args:
            page (int): Número de página
            per_page (int): Cantidad de productos por página
            include_variants (bool): Si es True, incluye las variantes de cada producto
            
        Returns:
            List[Dict]: Lista de productos con sus variantes
        """
        params = {'page': page, 'per_page': per_page}
        try:
            response = requests.get(f"{self.base_url}/products", headers=self.headers, params=params)
            response.raise_for_status()
            products = response.json()
            
            # Agregar store_id a cada producto
            for product in products:
                product['store_id'] = self.base_url.split('/')[-1]
            
            if include_variants:
                # Obtener variantes para cada producto
                for product in products:
                    product['variants'] = self.get_product_variants(product['id'])
            
            return products
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener productos: {e}")
            print(f"URL: {self.base_url}/products")
            print(f"Headers: {self.headers}")
            raise

    def get_product(self, product_id: int, include_variants: bool = True) -> Dict:
        """
        Obtiene los detalles de un producto específico.
        
        Args:
            product_id (int): ID del producto
            include_variants (bool): Si es True, incluye las variantes del producto
            
        Returns:
            Dict: Detalles del producto y sus variantes
        """
        try:
            response = requests.get(f"{self.base_url}/products/{product_id}", headers=self.headers)
            response.raise_for_status()
            product = response.json()
            
            # Agregar store_id al producto
            product['store_id'] = self.base_url.split('/')[-1]
            
            if include_variants:
                product['variants'] = self.get_product_variants(product_id)
                
            return product
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener el producto {product_id}: {e}")
            raise

    def get_product_variants(self, product_id: int) -> List[Dict]:
        """
        Obtiene las variantes de un producto específico.
        
        Args:
            product_id (int): ID del producto
            
        Returns:
            List[Dict]: Lista de variantes del producto
        """
        try:
            response = requests.get(f"{self.base_url}/products/{product_id}/variants", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener variantes del producto {product_id}: {e}")
            return []

    def create_product(self, product_data: Dict) -> Dict:
        """
        Crea un nuevo producto en la tienda.
        
        Args:
            product_data (Dict): Datos del producto a crear
            
        Returns:
            Dict: Datos del producto creado
        """
        try:
            response = requests.post(f"{self.base_url}/products", headers=self.headers, json=product_data)
            response.raise_for_status()
            product = response.json()
            # Agregar store_id al producto creado
            product['store_id'] = self.base_url.split('/')[-1]
            return product
        except requests.exceptions.RequestException as e:
            print(f"Error al crear el producto: {e}")
            raise

    def update_product(self, product_id: int, product_data: Dict) -> Dict:
        """
        Actualiza un producto existente.
        
        Args:
            product_id (int): ID del producto a actualizar
            product_data (Dict): Nuevos datos del producto
            
        Returns:
            Dict: Datos del producto actualizado
        """
        try:
            response = requests.put(f"{self.base_url}/products/{product_id}", headers=self.headers, json=product_data)
            response.raise_for_status()
            product = response.json()
            # Agregar store_id al producto actualizado
            product['store_id'] = self.base_url.split('/')[-1]
            return product
        except requests.exceptions.RequestException as e:
            print(f"Error al actualizar el producto {product_id}: {e}")
            raise

    def delete_product(self, product_id: int) -> None:
        """
        Elimina un producto.
        
        Args:
            product_id (int): ID del producto a eliminar
        """
        try:
            response = requests.delete(f"{self.base_url}/products/{product_id}", headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error al eliminar el producto {product_id}: {e}")
            raise 