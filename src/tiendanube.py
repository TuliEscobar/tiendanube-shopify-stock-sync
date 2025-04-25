import os
import json
import requests
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv
from .store_config import StoreConfig
import time
from datetime import datetime, timedelta
import pytz

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
        Obtiene los productos modificados en los últimos 15 minutos
        
        Returns:
            List[Dict]: Lista de productos actualizados
        """
        try:
            # Calcular tiempo hace 15 minutos con formato ISO 8601 exacto
            hora_actual = datetime.now(pytz.UTC)
            quince_minutos = hora_actual - timedelta(minutes=15)
            updated_at_min = quince_minutos.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            
            # Parámetros de consulta
            params = {
                'q': '',
                'per_page': 1,
                'published': "true",
                'min_stock': 1,
                'updated_at_min': updated_at_min
            }
            
            print(f"\n⏰ Información de fechas:")
            print(f"🔹 Hora actual UTC: {hora_actual.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z")
            print(f"🔹 Buscando desde: {updated_at_min}")
            
            response = self._make_request('GET', 'products', params=params)
            products = response.json()
            
            if not isinstance(products, list):
                print("❌ Respuesta inesperada de la API:")
                print(products)
                return []
            
            print(f"\n📦 Productos encontrados: {len(products)}")
            
            # Imprimir información detallada de cada producto
            for product in products:
                print(f"\n🔍 Producto:")
                print(f"   ID: {product.get('id')}")
                print(f"   Nombre: {product.get('name', {}).get('es', 'Sin nombre')}")
                ultima_actualizacion = product.get('updated_at', '')
                print(f"   Última actualización: {ultima_actualizacion}")
                
                # Verificar si el producto está dentro del rango de 15 minutos
                try:
                    # Convertir la fecha de actualización a objeto datetime
                    updated_at = datetime.strptime(ultima_actualizacion.replace('+0000', 'Z'), 
                                                 '%Y-%m-%dT%H:%M:%S%z')
                    diferencia = hora_actual - updated_at
                    minutos_diferencia = diferencia.total_seconds() / 60
                    print(f"   Minutos desde última actualización: {minutos_diferencia:.2f}")
                except Exception as e:
                    print(f"   ⚠️ Error procesando fecha: {str(e)}")
            
            # Filtrar productos con stock
            filtered_products = []
            for product in products:
                variants = product.get('variants', [])
                if variants:
                    has_stock = any(
                        variant.get('stock') is None or variant.get('stock', 0) > 0 
                        for variant in variants
                    )
                    if has_stock:
                        for variant in variants:
                            variant['sku'] = str(variant['id'])
                        filtered_products.append(product)
                else:
                    if product.get('stock') is None or product.get('stock', 0) > 0:
                        product['sku'] = str(product['id'])
                        filtered_products.append(product)
            
            print(f"\n✅ Productos con stock encontrados: {len(filtered_products)}")
            return filtered_products
            
        except Exception as e:
            print(f"❌ Error obteniendo productos: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Respuesta de la API: {e.response.text}")
            return []

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
            
