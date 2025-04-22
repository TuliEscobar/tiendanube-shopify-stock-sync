import json
import os
from typing import Dict, Optional, Tuple

class StockCacheManager:
    def __init__(self, cache_file: str = "stock_cache.json"):
        """
        Inicializa el gestor de caché de stock.
        
        Args:
            cache_file (str): Ruta al archivo de caché JSON
        """
        self.cache_file = cache_file
        self.cache_data = self._load_cache()
        self._migrate_old_format()
    
    def _migrate_old_format(self) -> None:
        """
        Migra el formato antiguo del caché al nuevo formato si es necesario.
        """
        needs_migration = False
        for value in self.cache_data.values():
            if not isinstance(value, dict):
                needs_migration = True
                break
        
        if needs_migration:
            migrated_data = {}
            for key, value in self.cache_data.items():
                migrated_data[key] = {
                    "tiendanube": value,
                    "shopify": value
                }
            self.cache_data = migrated_data
            self._save_cache()
    
    def _load_cache(self) -> Dict:
        """
        Carga el caché desde el archivo JSON o crea uno nuevo si no existe.
        
        Returns:
            Dict: Datos del caché
        """
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"[ADVERTENCIA] El archivo {self.cache_file} está corrupto. Creando nuevo caché.")
                return {}
        return {}
    
    def _save_cache(self) -> None:
        """Guarda el caché actual en el archivo JSON."""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
    
    def get_cached_stock(self, product_id: str, variant_id: str) -> Optional[Dict[str, int]]:
        """
        Obtiene el stock cacheado para un producto/variante.
        
        Args:
            product_id (str): ID del producto
            variant_id (str): ID de la variante
            
        Returns:
            Optional[Dict[str, int]]: Diccionario con stocks de ambas plataformas o None si no existe
        """
        key = f"{product_id}-{variant_id}"
        return self.cache_data.get(key)
    
    def update_stock(self, product_id: str, variant_id: str, tiendanube_stock: int, shopify_stock: int) -> None:
        """
        Actualiza el stock en el caché para ambas plataformas.
        
        Args:
            product_id (str): ID del producto
            variant_id (str): ID de la variante
            tiendanube_stock (int): Stock actual en Tiendanube
            shopify_stock (int): Stock actual en Shopify
        """
        key = f"{product_id}-{variant_id}"
        self.cache_data[key] = {
            "tiendanube": tiendanube_stock,
            "shopify": shopify_stock
        }
        self._save_cache()
    
    def should_update_shopify(self, product_id: str, variant_id: str, 
                            tiendanube_stock: int, shopify_stock: int) -> bool:
        """
        Determina si se debe actualizar el stock en Shopify.
        Solo actualiza si el stock en Tiendanube cambió respecto al caché.
        
        Args:
            product_id (str): ID del producto
            variant_id (str): ID de la variante
            tiendanube_stock (int): Stock actual en TiendaNube
            shopify_stock (int): Stock actual en Shopify
            
        Returns:
            bool: True si se debe actualizar Shopify
        """
        cached = self.get_cached_stock(product_id, variant_id)
        
        # Si no hay caché, siempre actualizar
        if cached is None:
            return True
        
        # Solo actualizamos si el stock de TiendaNube cambió respecto al caché
        return tiendanube_stock != cached["tiendanube"]
    
    def should_update_tiendanube(self, product_id: str, variant_id: str, 
                               current_stock: int, shopify_stock: int) -> bool:
        """
        Determina si se debe actualizar el stock en Tiendanube.
        Solo actualiza si el stock en Shopify disminuyó respecto al caché.
        
        Args:
            product_id (str): ID del producto
            variant_id (str): ID de la variante
            current_stock (int): Stock actual en Tiendanube
            shopify_stock (int): Stock actual en Shopify
            
        Returns:
            bool: True si se debe actualizar Tiendanube
        """
        cached = self.get_cached_stock(product_id, variant_id)
        
        # Si no hay stock en caché, no actualizamos
        if cached is None:
            return False
            
        # Solo actualizamos Tiendanube si:
        # 1. No hubo cambios en Tiendanube (stock actual = cache)
        # 2. El stock en Shopify disminuyó respecto al caché
        return (current_stock == cached["tiendanube"] and 
                shopify_stock < cached["shopify"])
    
    def get_all_cached_products(self) -> Dict[str, Dict[str, int]]:
        """
        Obtiene todos los productos en caché.
        
        Returns:
            Dict[str, Dict[str, int]]: Diccionario con todos los productos y sus stocks en ambas plataformas
        """
        return self.cache_data.copy()