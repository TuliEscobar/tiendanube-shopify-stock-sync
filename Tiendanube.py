import requests # type: ignore
import itertools

from concurrent.futures import ThreadPoolExecutor


class Tiendanube:

    def __init__(self, credentials):
        self.credentials = credentials

    def fetch_data(self, endpoint):
        """Hace solicitudes GET en paralelo a un endpoint específico."""
        def request(credential):
            try:
                url = f"{credential['base_url']}/{endpoint}"
                response = requests.get(url, headers=credential["headers"])
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                return [{"error": str(e)}]

        with ThreadPoolExecutor() as executor:
            results = list(executor.map(request, self.credentials))

        return list(itertools.chain.from_iterable(results))

    def get_products(self):
        """Obtiene los productos desde la API."""
        return self.fetch_data("products")

    def get_categories(self):
        """Obtiene las categorías desde la API."""
        return self.fetch_data("categories?fields=id,name,description,parent,subcategories")

    def get_variants(self):
        """Obtiene las categorías desde la API."""
        variants = self.fetch_data("products?fields=variants")
        data = []
        for variant in variants:
            data.append(variant['variants'])
        return list(itertools.chain.from_iterable(data))

