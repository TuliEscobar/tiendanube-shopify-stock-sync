from typing import Dict, Optional, List
import os
import json
from dotenv import load_dotenv

class StoreConfig:
    def __init__(self):
        """
        Inicializa la configuración de tiendas desde el archivo .env
        """
        load_dotenv()
        self.stores = self._load_stores()
        
    def _load_stores(self) -> List[Dict]:
        """
        Carga la configuración de tiendas desde .env
        
        Returns:
            List[Dict]: Lista de configuraciones de tiendas
        """
        try:
            # Obtener las credenciales de Tiendanube del .env
            tiendanube_credentials = os.getenv('TIENDANUBE_CREDENTIALS')
            if not tiendanube_credentials:
                raise ValueError("No se encontraron las credenciales de Tiendanube en .env")
            
            # Convertir el string JSON a lista de diccionarios
            stores = json.loads(tiendanube_credentials)
            
            # Formatear las tiendas al formato esperado
            formatted_stores = []
            for store in stores:
                formatted_store = {
                    'api_url': store['base_url'],
                    'token': store['headers']['Authentication'],
                    'user_agent': store['headers']['User-Agent'] or 'Conexion a Tienda Nube (devs.tiendaonline@gmail.com)',
                    'category': 'todo'  # Categoría por defecto
                }
                formatted_stores.append(formatted_store)
            
            return formatted_stores
            
        except Exception as e:
            raise Exception(f"Error al cargar las credenciales desde .env: {str(e)}")
    
    def get_store_config(self, api_url: str) -> Dict[str, any]:
        """
        Obtiene la configuración de una tienda específica por su URL de API.
        
        Args:
            api_url (str): URL de la API de la tienda
            
        Returns:
            Dict[str, any]: Diccionario con la configuración de la tienda
        """
        for store in self.stores:
            if store['api_url'] == api_url:
                return store
        raise ValueError(f"No se encontró la tienda con URL: {api_url}")
    
    def get_all_stores(self) -> List[Dict]:
        """
        Retorna la lista de todas las tiendas configuradas
        
        Returns:
            List[Dict]: Lista de configuraciones de tiendas
        """
        return self.stores
    
    def get_stores_by_category(self, category: str) -> list:
        """
        Obtiene la lista de tiendas filtradas por categoría.
        
        Args:
            category (str): Categoría de las tiendas a filtrar
            
        Returns:
            list: Lista de diccionarios con la configuración de las tiendas de la categoría
        """
        return [
            store for store in self.stores 
            if store['category'].lower() == category.lower()
        ] 