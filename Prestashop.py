from io import BytesIO
import requests
import xml.etree.ElementTree as ET

from .Utils import Utils

class Prestashop():

    def __init__(self, API_BASE_URL, AUTH, HEADERS):
        self.API_BASE_URL = API_BASE_URL
        self.AUTH = AUTH
        self.HEADERS = HEADERS

    ##############
    ## PRODUCTS ##
    ##############

    def get_products(self):
        """Get all products from Prestashop API.

        Returns:
            list: List of products.
        """
        url_prestashop = f"{self.API_BASE_URL}/products?output_format=JSON&display=[id,mpn]&sort=[id_ASC]"
        response = requests.get(url_prestashop, auth=self.AUTH)

        data = []
        if response.status_code == 200:
            data = response.json()["products"]
        else:
            Utils.report_error({
                "name": "get_id_products",
                "status_code": response.status_code,
                "response": response.json()
            })

        return data

    def get_product(self, id):
        """Get a product from Prestashop API.

        Args:
            id (str): Product ID.

        Returns:
            dict: Product data.
        """
        url_prestashop = f"{self.API_BASE_URL}/products/{id}?output_format=JSON&display=full"
        response = requests.get(url_prestashop, auth=self.AUTH)

        data = {}
        if response.status_code == 200:
            data = response.json()
        else:
            Utils.report_error({
                "name": "get_product",
                "status_code": response.status_code,
                "response": response.json()
            })

        return data

    def update_product(self, id, body):
        """Update a product in Prestashop API.

        Args:
            data (dict): Product data.

        Returns:
            bool: True if the product was updated successfully, False otherwise.
        """
        url_prestashop = f"{self.API_BASE_URL}/products/{id}"
        xml_body = body

        response = requests.patch(url_prestashop, auth=self.AUTH, headers=self.HEADERS, data=xml_body)

        if response.status_code in [200, 201]:
            print("✅ Producto actualizado correctamente.")
            tree = ET.ElementTree(ET.fromstring(response.content))
            new_id = tree.find(".//id").text
            return new_id
        else:
            Utils.report_error({
                "name": "update_product",
                "status_code": response.status_code,
                "response": response.content
            })
            return False

    def create_product(self, body):
        """Create a product in Prestashop API.

        Args:
            data (dict): Product data.

        Returns:
            bool: True if the product was created successfully, False otherwise.
        """
        url_prestashop = f"{self.API_BASE_URL}/products"
        xml_body = body

        response = requests.post(url_prestashop, auth=self.AUTH, headers=self.HEADERS, data=xml_body)

        if response.status_code in [200, 201]:
            print("✅ Producto creado correctamente.")
            tree = ET.ElementTree(ET.fromstring(response.content))
            new_id = tree.find(".//id").text
            return new_id
        else:
            data = {
                "name": "create_product",
                "status_code": response.status_code
            }
            try:
                response = response.json()
            except Exception as e:
                response = response.content
            data["response"] = response
            Utils.report_error(data)
            return False

    #####################
    ## STOCK AVAILABLE ##
    #####################

    def get_stock_availables(self):
        """Get all stock availables from Prestashop API.

        Returns:
            dict: dict of stock availables. key: product_id, value: stock_id.
        """
        url_prestashop = f"{self.API_BASE_URL}/stock_availables?display=[id,id_product,id_product_attribute]&output_format=JSON"
        response = requests.get(url_prestashop, auth=self.AUTH)

        if response.status_code == 200:
            return response.json()["stock_availables"]
        else:
            Utils.report_error({
                "name": "get_stock_availables",
                "status_code": response.status_code,
                "response": response.text
            })

    def update_stock(self, id, body):
        """Update a product stock in Prestashop API.

        Args:
            data (dict): Product data.

        Returns:
            bool: True if the product stock was updated successfully, False otherwise.
        """
        url_prestashop = f"{self.API_BASE_URL}/stock_availables/{id}"
        xml_body = body

        response = requests.patch(url_prestashop, auth=self.AUTH, headers=self.HEADERS, data=xml_body)

        if response.status_code in [200, 201]:
            print("✅ Stock actualizado correctamente.")
            return True
        else:
            Utils.report_error({
                "name": "update_stock",
                "status_code": response.status_code,
                "response": response.json()
            })
            return False

    ################
    ## CATEGORIES ##
    ################

    def get_categories(self):
        """Get all categories from Prestashop API.

        Returns:
            list: List of categories.
        """
        url_prestashop = f"{self.API_BASE_URL}/categories?output_format=JSON&display=[id,name]"
        response = requests.get(url_prestashop, auth=self.AUTH)

        data = []
        if response.status_code == 200:
            data = response.json()
        else:
            Utils.report_error({
                "name": "get_categories",
                "status_code": response.status_code,
                "response": response.json()
            })

        return data['categories']

    def create_category(self, name, parent=2):
        """Create a category in Prestashop API.

        Args:
            name (str): Name of the category.
            description (str, optional): Description of the category. Defaults to None.
        """
        url_prestashop = f"{self.API_BASE_URL}/categories"
        # TODO talvez el body debria crearse en Utils.py
        # el parent = 2 no tengo idea porque es asi pero funciona
        xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
            <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
            <category>
                <name>
                    <language id="2"><![CDATA[{name}]]></language>
                </name>
                <link_rewrite>
                    <language id="2"><![CDATA[{name}]]></language>
                </link_rewrite>
                <description>
                    <language id="2"><![CDATA[{name}]]></language>
                </description>
                <active>1</active>
                <id_parent>{parent}</id_parent>
            </category>
            </prestashop>
        """
        response = requests.post(url_prestashop, auth=self.AUTH, headers=self.HEADERS, data=xml_body)

        if response.status_code in [200, 201]:
        # Extraer el ID de la nueva categoría creada
            tree = ET.ElementTree(ET.fromstring(response.content))
            new_id = tree.find(".//id").text
            print(f"✅ Categoría '{name}' creada con ID {new_id} en PrestaShop.")
            return new_id
        else:
            print(f"❌ Error al crear la categoría '{name}': {response.content}")
            return None
        

    ############
    ## IMAGES ##
    ############

    def get_images_id_of_product(self, product_id):
        url = f"{self.API_BASE_URL}/images/products/{product_id}"
        response = requests.get(url, auth=self.AUTH)

        if response.status_code == 200:
            root = ET.fromstring(response.content)
            return [declination.get("id") for declination in root.findall(".//declination")]
        else:
            print(f"❌ Error al obtener las imagen: {response.status_code}: {response.content}")
            print()

    def create_image(self, image_url, product_id):
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            image_data = BytesIO(response.content)
            image_data.seek(0)
        else:
            print(f"❌ Error al descargar la imagen: {response.status_code}")
            exit()

        url_prestashop = f"{self.API_BASE_URL}/images/products/{product_id}"
        files = {"image": ("image.jpg", image_data, "image/jpeg")}
        response = requests.post(url_prestashop, files=files, auth=self.AUTH)

        if response.status_code in [200, 201]:
            print("✅ Imagen subida exitosamente a PrestaShop.")
            tree = ET.ElementTree(ET.fromstring(response.content))
            new_id = tree.find(".//id").text
            return new_id
        else:
            print(f"❌ Error al subir la imagen: {response.text}")

    def delete_images(self, product_id, image_id):
        url_prestashop = f"{self.API_BASE_URL}/images/products/{product_id}/{image_id}"
        response = requests.delete(url=url_prestashop, auth=self.AUTH)

        if response.status_code != 200:
            print(f"❌ Error al eliminar la imagen: {response.text}")


    ##################
    ## COMBINATIONS ##
    ##################

    def get_combinations(self, product_id=None):
        url_prestashop = f"{self.API_BASE_URL}/combinations?output_format=JSON&display=[id,id_product,mpn]"
        if product_id:
            url_prestashop += f"&filter[id_product]={product_id}"
        response = requests.get(url_prestashop, auth=self.AUTH)

        if response.status_code == 200:
            return response.json()['combinations']
        else:
            print(f"❌ Error al obtener la combinacion: {response.text}")


    def create_combinations(self, body):
        url_prestashop = f"{self.API_BASE_URL}/combinations"
        xml_body = body

        response = requests.post(url_prestashop, data=xml_body, headers=self.HEADERS, auth=self.AUTH)

        if response.status_code in [200, 201]:
            print("✅ Combinacion creada exitosamente en PrestaShop.")
            tree = ET.ElementTree(ET.fromstring(response.content))
            new_id = tree.find(".//id").text
            return new_id
        else:
            print(f"❌ Error al crear la combinacion: {response.text}")

    def update_combination(self, id_combination, body):
        url_prestashop = f"{self.API_BASE_URL}/combinations/{id_combination}"
        xml_body = body
        
        response = requests.patch(url_prestashop, data=xml_body, headers=self.HEADERS, auth=self.AUTH)

        if response.status_code in [200, 201]:
            print("✅ Combinacion editada exitosamente en PrestaShop.")
            tree = ET.ElementTree(ET.fromstring(response.content))
            new_id = tree.find(".//id").text
            return new_id
        else:
            print(f"❌ Error al actualizar la combinacion: {response.text}")



    ###############################################
    ## PRODUCT OPTIONS AND PRODUCT OPTION VALUES ##
    ###############################################

    def get_product_options(self):
        url_prestashop = f"{self.API_BASE_URL}/product_options?output_format=JSON&display=full"
        response = requests.get(url=url_prestashop, headers=self.HEADERS, auth=self.AUTH)

        if response.status_code == 200:
            return response.json()['product_options']
        else:
            print(f"❌ Error al obtener option_values: {response.text}")

    def get_product_option_values(self):
        url_prestashop = f"{self.API_BASE_URL}/product_option_values?output_format=JSON&display=[id, name]"
        response = requests.get(url=url_prestashop, headers=self.HEADERS, auth=self.AUTH)

        if response.status_code == 200:
            return response.json()['product_option_values']
        else:
            print(f"❌ Error al obtener option_values: {response.text}")

    def create_product_option(self, body):
        url = f"{self.API_BASE_URL}/product_options"
        response = requests.post(url, data=body, headers=self.HEADERS, auth=self.AUTH)

        if response.status_code in [200, 201]:
            print("✅ Product_options creada exitosamente en PrestaShop.")
            tree = ET.ElementTree(ET.fromstring(response.content))
            new_id = tree.find(".//id").text
            return new_id
        else:
            print(f"❌ Error al crear product_options: {response.text}")

    def create_product_option_value(self, body):
        url = f"{self.API_BASE_URL}/product_option_values"
        response = requests.post(url, data=body, headers=self.HEADERS, auth=self.AUTH)

        if response.status_code in [200, 201]:
            print("✅ Product_option_values creada exitosamente en PrestaShop.")
            tree = ET.ElementTree(ET.fromstring(response.content))
            new_id = tree.find(".//id").text
            return new_id
        else:
            print(f"❌ Error al crear product_option_values: {response.text}")
