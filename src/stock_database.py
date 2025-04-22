import os
import json
from typing import Dict, Optional
from datetime import datetime

class StockDatabase:
    def __init__(self):
        """Inicializa la base de datos de stock"""
        # Obtener el directorio raíz del proyecto (un nivel arriba de src)
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_file = os.path.join(root_dir, 'stock_history.json')
        self.stocks = self._load_database()
        
        # Crear el directorio si no existe
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        
        print(f"📁 Base de datos de stock en: {self.db_file}")
    
    def _load_database(self) -> Dict:
        """Carga la base de datos desde el archivo JSON"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✅ Base de datos cargada: {len(data.get('stores', {}))} tiendas")
                    return data
            except Exception as e:
                print(f"⚠️ Error al cargar la base de datos: {str(e)}")
                return {'stores': {}}
        return {'stores': {}}
    
    def _save_database(self):
        """Guarda la base de datos en el archivo JSON"""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.stocks, f, indent=2)
    
    def get_last_stock(self, store_id: str, sku: str) -> Optional[Dict]:
        """
        Obtiene el último registro de stock para un producto
        
        Args:
            store_id (str): ID de la tienda
            sku (str): SKU del producto
            
        Returns:
            Optional[Dict]: Último registro de stock o None si no existe
        """
        store_data = self.stocks['stores'].get(store_id, {})
        return store_data.get(sku)
    
    def update_stock(self, store_id: str, sku: str, tiendanube_stock: int, shopify_stock: int):
        """
        Actualiza el registro de stock de un producto
        
        Args:
            store_id (str): ID de la tienda
            sku (str): SKU del producto
            tiendanube_stock (int): Stock actual en Tiendanube
            shopify_stock (int): Stock actual en Shopify
        """
        # Asegurar que existe la estructura para la tienda
        if store_id not in self.stocks['stores']:
            self.stocks['stores'][store_id] = {}
        
        # Obtener el registro anterior si existe
        current_record = self.stocks['stores'][store_id].get(sku, {
            'history': []
        })
        
        # Crear nuevo registro
        new_record = {
            'timestamp': datetime.now().isoformat(),
            'tiendanube_stock': tiendanube_stock,
            'shopify_stock': shopify_stock
        }
        
        # Agregar al historial
        current_record['history'].append(new_record)
        
        # Mantener solo los últimos 10 registros
        if len(current_record['history']) > 10:
            current_record['history'] = current_record['history'][-10:]
        
        # Actualizar el registro actual
        current_record['current_tiendanube_stock'] = tiendanube_stock
        current_record['current_shopify_stock'] = shopify_stock
        current_record['last_update'] = new_record['timestamp']
        
        # Guardar en la base de datos
        self.stocks['stores'][store_id][sku] = current_record
        self._save_database()
    
    def get_stock_history(self, store_id: str, sku: str, limit: int = 10) -> list:
        """
        Obtiene el historial de stock de un producto
        
        Args:
            store_id (str): ID de la tienda
            sku (str): SKU del producto
            limit (int): Número máximo de registros a devolver
            
        Returns:
            list: Lista de registros históricos
        """
        store_data = self.stocks['stores'].get(store_id, {})
        product_data = store_data.get(sku, {})
        history = product_data.get('history', [])
        return history[-limit:]
    
    def has_stock_changed(self, store_id: str, sku: str, tiendanube_stock: int) -> bool:
        """
        Verifica si el stock ha cambiado respecto al último registro
        
        Args:
            store_id (str): ID de la tienda
            sku (str): SKU del producto
            tiendanube_stock (int): Stock actual en Tiendanube
            
        Returns:
            bool: True si el stock ha cambiado, False si no
        """
        last_record = self.get_last_stock(store_id, sku)
        if not last_record:
            return True
            
        return last_record.get('current_tiendanube_stock') != tiendanube_stock 