import os
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Cargar configuración desde .env
TIENDANUBE_CREDENTIALS = eval(os.getenv('TIENDANUBE_CREDENTIALS', '[]'))

class TiendanubeAPI:
    def __init__(self, store_number: int = 1):
        """
        Inicializa el cliente de Tiendanube para una tienda específica.
        
        Args:
            store_number (int): Número de la tienda (1-4, índice basado en 1)
        """
        if not 1 <= store_number <= len(TIENDANUBE_CREDENTIALS):
            raise ValueError(f"Número de tienda inválido. Debe estar entre 1 y {len(TIENDANUBE_CREDENTIALS)}")
        
        # Obtener credenciales de la tienda (restamos 1 porque el índice está basado en 0)
        store_config = TIENDANUBE_CREDENTIALS[store_number - 1]
        
        self.api_url = store_config['base_url']
        # Extraer el store_id de la URL base (último segmento)
        self.store_id = self.api_url.split('/')[-1]
        self.headers = {
            **store_config['headers'],
            'Content-Type': 'application/json'
        }

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
            response = requests.get(f"{self.api_url}/products", headers=self.headers, params=params)
            response.raise_for_status()
            products = response.json()
            
            # Agregar store_id a cada producto
            for product in products:
                product['store_id'] = self.store_id
            
            if include_variants:
                # Obtener variantes para cada producto
                for product in products:
                    product['variants'] = self.get_product_variants(product['id'])
            
            return products
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener productos: {e}")
            print(f"URL: {self.api_url}/products")
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
            response = requests.get(f"{self.api_url}/products/{product_id}", headers=self.headers)
            response.raise_for_status()
            product = response.json()
            
            # Agregar store_id al producto
            product['store_id'] = self.store_id
            
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
            response = requests.get(f"{self.api_url}/products/{product_id}/variants", headers=self.headers)
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
            response = requests.post(f"{self.api_url}/products", headers=self.headers, json=product_data)
            response.raise_for_status()
            product = response.json()
            # Agregar store_id al producto creado
            product['store_id'] = self.store_id
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
            response = requests.put(f"{self.api_url}/products/{product_id}", headers=self.headers, json=product_data)
            response.raise_for_status()
            product = response.json()
            # Agregar store_id al producto actualizado
            product['store_id'] = self.store_id
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
            response = requests.delete(f"{self.api_url}/products/{product_id}", headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error al eliminar el producto {product_id}: {e}")
            raise 