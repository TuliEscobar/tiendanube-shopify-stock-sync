import requests
from typing import Dict, List, Optional
from . import settings

class TiendanubeAPI:
    def __init__(self, access_token: str, store_id: str):
        self.access_token = access_token
        self.store_id = store_id
        self.base_url = f'https://api.tiendanube.com/v1/{store_id}'
        self.headers = {
            'Authentication': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def get_products(self, page: int = 1, per_page: int = 50) -> List[Dict]:
        """Obtiene la lista de productos de la tienda."""
        url = f'{self.base_url}/products'
        params = {
            'page': page,
            'per_page': per_page
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_product(self, product_id: int) -> Dict:
        """Obtiene los detalles de un producto específico."""
        url = f'{self.base_url}/products/{product_id}'
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def create_product(self, product_data: Dict) -> Dict:
        """Crea un nuevo producto en la tienda."""
        url = f'{self.base_url}/products'
        
        response = requests.post(url, headers=self.headers, json=product_data)
        response.raise_for_status()
        
        return response.json()
    
    def update_product(self, product_id: int, product_data: Dict) -> Dict:
        """Actualiza un producto existente."""
        url = f'{self.base_url}/products/{product_id}'
        
        response = requests.put(url, headers=self.headers, json=product_data)
        response.raise_for_status()
        
        return response.json()
    
    def delete_product(self, product_id: int) -> None:
        """Elimina un producto."""
        url = f'{self.base_url}/products/{product_id}'
        
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status() 