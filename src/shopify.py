import shopify
from typing import Dict, List, Optional
from . import settings

class ShopifyAPI:
    def __init__(self, shop_url: str, access_token: str):
        self.shop_url = shop_url
        self.access_token = access_token
        shopify.ShopifyResource.set_site(f"https://{shop_url}/admin/api/2024-01")
        shopify.ShopifyResource.set_headers({'X-Shopify-Access-Token': access_token})
    
    def get_products(self, page: int = 1, limit: int = 50) -> List[Dict]:
        """Obtiene la lista de productos de la tienda."""
        products = shopify.Product.find(
            page=page,
            limit=limit
        )
        return [product.to_dict() for product in products]
    
    def get_product(self, product_id: int) -> Dict:
        """Obtiene los detalles de un producto específico."""
        product = shopify.Product.find(product_id)
        return product.to_dict()
    
    def create_product(self, product_data: Dict) -> Dict:
        """Crea un nuevo producto en la tienda."""
        product = shopify.Product(product_data)
        product.save()
        return product.to_dict()
    
    def update_product(self, product_id: int, product_data: Dict) -> Dict:
        """Actualiza un producto existente."""
        product = shopify.Product.find(product_id)
        for key, value in product_data.items():
            setattr(product, key, value)
        product.save()
        return product.to_dict()
    
    def delete_product(self, product_id: int) -> None:
        """Elimina un producto."""
        product = shopify.Product.find(product_id)
        product.destroy() 