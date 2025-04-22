from typing import Dict, Optional, List
import pandas as pd
from pathlib import Path
import os

class StoreConfig:
    def __init__(self, excel_path: str = "tiendas.xlsx"):
        """
        Inicializa la configuración de tiendas desde un archivo Excel
        
        Args:
            excel_path (str): Ruta al archivo Excel
        """
        self.excel_path = self._find_excel_file(excel_path)
        self.stores = self._load_stores()
        
    def _find_excel_file(self, excel_name: str) -> str:
        """
        Busca el archivo Excel en el directorio actual y en src/
        
        Args:
            excel_name (str): Nombre del archivo Excel
            
        Returns:
            str: Ruta completa al archivo Excel
        """
        # Buscar en el directorio actual
        if os.path.exists(excel_name):
            return os.path.abspath(excel_name)
        
        # Buscar en el directorio src/
        src_path = os.path.join("src", excel_name)
        if os.path.exists(src_path):
            return os.path.abspath(src_path)
        
        # Buscar en el directorio padre si estamos en src/
        parent_path = os.path.join("..", excel_name)
        if os.path.exists(parent_path):
            return os.path.abspath(parent_path)
        
        raise FileNotFoundError(f"No se encontró el archivo Excel '{excel_name}'")

    def _load_stores(self) -> List[Dict]:
        """
        Carga la configuración de tiendas desde el Excel
        
        Returns:
            List[Dict]: Lista de configuraciones de tiendas
        """
        try:
            # Leer el Excel sin usar la primera fila como nombres de columnas
            df = pd.read_excel(self.excel_path, header=None)
            
            # Verificar que tenga al menos 12 columnas
            if len(df.columns) < 12:
                raise ValueError("El Excel debe tener al menos 12 columnas")
            
            # Renombrar las columnas para mejor manejo
            df.columns = ['api_url', 'token', 'user_agent'] + [f'col{i}' for i in range(4, len(df.columns) + 1)]
            
            # Eliminar filas con URLs vacías
            df = df.dropna(subset=['api_url'])
            
            # Convertir a lista de diccionarios
            stores = []
            for _, row in df.iterrows():
                # Limpiar y formatear el token
                token = str(row['token']).strip()
                if not token.lower().startswith('bearer '):
                    token = f"bearer {token}"
                
                store = {
                    'api_url': str(row['api_url']).strip(),
                    'token': token,
                    'user_agent': 'Conexion a Tienda Nube (devs.tiendaonline@gmail.com)',
                    'category': str(row.get('col12', 'todo')).strip()
                }
                stores.append(store)
            
            return stores
            
        except Exception as e:
            raise Exception(f"Error al cargar el Excel: {str(e)}")
    
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