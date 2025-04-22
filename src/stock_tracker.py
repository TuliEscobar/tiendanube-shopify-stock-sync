import os
import json
from typing import Dict, Optional

class StockTracker:
    def __init__(self):
        self.cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_cache.json')
        self.last_stocks = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Carga el último estado conocido del stock desde el archivo cache"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Guarda el estado actual del stock en el archivo cache"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.last_stocks, f, indent=2)
    
    def get_last_stock(self, store_id: str, product_id: str) -> Optional[int]:
        """Obtiene el último stock conocido de un producto"""
        store_data = self.last_stocks.get(store_id, {})
        return store_data.get(product_id)
    
    def update_stock(self, store_id: str, product_id: str, stock: int):
        """Actualiza el stock de un producto en el cache"""
        if store_id not in self.last_stocks:
            self.last_stocks[store_id] = {}
        self.last_stocks[store_id][product_id] = stock
        self._save_cache() 