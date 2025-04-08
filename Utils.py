import xml.etree.ElementTree as ET

class Utils:

    def __init__(self):
        pass

    @staticmethod
    def body_update_product(json_data, prestashop_category_map):
        root = ET.Element("prestashop", attrib={"xmlns:xlink": "http://www.w3.org/1999/xlink"})
        product = ET.SubElement(root, "product")

        ET.SubElement(product, "id").text = f"<![CDATA[{json_data['id']}]]>"

        name = ET.SubElement(product, "name")
        lang = ET.SubElement(name, "language", attrib={"id": "2"})
        lang.text = f"<![CDATA[{json_data['name']['es']}]]>"

        description = ET.SubElement(product, "description")
        lang = ET.SubElement(description, "language", attrib={"id": "2"})
        lang.text = f"<![CDATA[{json_data['description']['es']}]]>"

        variant = json_data['variants'][0] if json_data['variants'] else {}

        ET.SubElement(product, "width").text = f"<![CDATA[{variant.get('width', '0')}]]>"
        ET.SubElement(product, "height").text = f"<![CDATA[{variant.get('height', '0')}]]>"
        ET.SubElement(product, "depth").text = f"<![CDATA[{variant.get('depth', '0')}]]>"
        ET.SubElement(product, "weight").text = f"<![CDATA[{variant.get('weight', '0')}]]>"
        ET.SubElement(product, "active").text = "<![CDATA[1]]>"
        ET.SubElement(product, "price").text = f"<![CDATA[{variant.get('price', '0.00')}]]>"
        ET.SubElement(product, "visibility").text = "<![CDATA[both]]>"

        associations = ET.SubElement(product, "associations")
        categories = ET.SubElement(associations, "categories", attrib={"nodeType": "category", "api": "categories"})

        for idx, cat in enumerate(json_data.get('categories', []), start=1):
            if cat['name']['es'].lower() in prestashop_category_map.keys():
                category_id = prestashop_category_map[cat['name']['es'].lower()]
            else:
                category_id = 1

            category = ET.SubElement(categories, "category", attrib={"xlink:href": f"https://tiendaonline.com/api/categories/{category_id}"})
            ET.SubElement(category, "id").text = f"<![CDATA[{category_id}]]>"

        # TODO tengo que subir la imagen primero y despues relacionarla
        images = ET.SubElement(associations, "images", attrib={"nodeType": "image", "api": "images"})
        for image in json_data.get('images', []):
            img_elem = ET.SubElement(images, "image", attrib={"xlink:href": image['src']})
            ET.SubElement(img_elem, "id").text = f"<![CDATA[{image['id']}]]>"

        return ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")

    @staticmethod
    def body_desactivate_product(id):
        root = ET.Element("prestashop", attrib={"xmlns:xlink": "http://www.w3.org/1999/xlink"})
        product = ET.SubElement(root, "product")

        ET.SubElement(product, "id").text = f"<![CDATA[{id}]]>"
        ET.SubElement(product, "active").text = "<![CDATA[0]]>"

        return ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")

    @staticmethod
    def body_create_product(json_data, prestashop_category_map, id_product=None):
        root = ET.Element("prestashop", attrib={"xmlns:xlink": "http://www.w3.org/1999/xlink"})

        product = ET.SubElement(root, "product")

        if id_product:
            ET.SubElement(product, "id").text = f"<![CDATA[{id_product}]]>"
        ET.SubElement(product, "id_manufacturer").text = "<![CDATA[1]]>"
        ET.SubElement(product, "new").text = "<![CDATA[1]]>"
        ET.SubElement(product, "price").text = f"<![CDATA[{json_data['variants'][0]['price']}]]>"
        ET.SubElement(product, "weight").text = f"<![CDATA[{json_data['variants'][0]['weight']}]]>"
        ET.SubElement(product, "width").text = f"<![CDATA[{json_data['variants'][0]['width']}]]>"
        ET.SubElement(product, "height").text = f"<![CDATA[{json_data['variants'][0]['height']}]]>"
        ET.SubElement(product, "depth").text = f"<![CDATA[{json_data['variants'][0]['depth']}]]>"
        ET.SubElement(product, "active").text = "<![CDATA[1]]>"
        ET.SubElement(product, "visibility").text = "<![CDATA[both]]>"
        ET.SubElement(product, "redirect_type").text = "<![CDATA[default]]>"
        ET.SubElement(product, "available_for_order").text = "<![CDATA[1]]>"
        ET.SubElement(product, "show_price").text = "<![CDATA[1]]>"
        ET.SubElement(product, "state").text = "<![CDATA[1]]>"
        ET.SubElement(product, "mpn").text = str(json_data['id'])

        name = ET.SubElement(product, "name")
        lang = ET.SubElement(name, "language", attrib={"id": "2"})
        lang.text = f"<![CDATA[{json_data['name']['es']}]]>"

        description = ET.SubElement(product, "description")
        lang_desc = ET.SubElement(description, "language", attrib={"id": "2"})
        lang_desc.text = f"<![CDATA[{json_data['description']['es']}]]>"

        associations = ET.SubElement(product, "associations")
        categories = ET.SubElement(associations, "categories", attrib={"nodeType": "category", "api": "categories"})

        category_id = 2
        for idx, cat in enumerate(json_data.get('categories', []), start=1):
            if cat['name']['es'].lower() in prestashop_category_map.keys():
                category_id = prestashop_category_map[cat['name']['es'].lower()]

            category = ET.SubElement(categories, "category", attrib={"xlink:href": f"https://tiendaonline.com/api/categories/{category_id}"})
            ET.SubElement(category, "id").text = f"<![CDATA[{category_id}]]>"

        ET.SubElement(product, "id_category_default").text = str(category_id)

        return ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")

    @staticmethod
    def body_update_stock(data):
        return f"""<?xml version="1.0" encoding="UTF-8"?>
            <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
                <stock_available>
                    <id><![CDATA[{data['stock_id']}]]></id>
                    <quantity><![CDATA[{data['quantity']}]]></quantity>
                </stock_available>
            </prestashop>
        """

    @staticmethod
    def body_combination(data, product_id, product_option_value_id, image_id=None, combination_id=None):
        # Crear el elemento raíz <prestashop>
        root = ET.Element("prestashop", attrib={"xmlns:xlink": "http://www.w3.org/1999/xlink"})

        # Crear el elemento <combination>
        combination = ET.SubElement(root, "combination")

        if combination_id:
            ET.SubElement(combination, "id").text = f"<![CDATA[{combination_id}]]>"
        ET.SubElement(combination, "id_product").text = f"<![CDATA[{product_id}]]>"
        ET.SubElement(combination, "ean13").text = "<![CDATA[]]>"
        ET.SubElement(combination, "mpn").text = f"<![CDATA[{data['id']}]]>"
        ET.SubElement(combination, "reference").text = "<![CDATA[]]>"
        ET.SubElement(combination, "supplier_reference").text = "<![CDATA[]]>"
        ET.SubElement(combination, "price").text = f"<![CDATA[{data['price']}]]>"
        ET.SubElement(combination, "minimal_quantity").text = "<![CDATA[0]]>"

        # Crear <associations>
        associations = ET.SubElement(combination, "associations")

        # Agregar <product_option_values>
        option_values = ET.SubElement(associations, "product_option_values", attrib={
            "nodeType": "product_option_value", "api": "product_option_values"
        })
        option_value = ET.SubElement(option_values, "product_option_value")
        ET.SubElement(option_value, "id").text = f"<![CDATA[{product_option_value_id}]]>"

        # Agregar <images>
        if image_id:
            images = ET.SubElement(associations, "images")
            image = ET.SubElement(images, "image")
            ET.SubElement(image, "id").text = f"<![CDATA[{image_id}]]>"

        # Convertir el árbol XML a una cadena
        return ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")

    @staticmethod
    def body_combination_update(data, image_id, product_option_value_id, combination_id):
        body = f"""<?xml version="1.0" encoding="UTF-8"?>
            <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
                <combination>
                    <id><![CDATA[{combination_id}]]></id>
                    <ean13><![CDATA[]]></ean13>
                    <mpn><![CDATA[{data['id']}]]></mpn>
                    <reference><![CDATA[]]></reference>
                    <supplier_reference><![CDATA[]]></supplier_reference>
                    <price><![CDATA[{data['price']}]]></price>
                    <minimal_quantity><![CDATA[0]]></minimal_quantity>
                    <associations>
                        <product_option_values nodeType="product_option_value" api="product_option_values">
                            <product_option_value>
                                <id><![CDATA[{product_option_value_id}]]></id>
                            </product_option_value>
                        </product_option_values>
                        <images>
                            <image>
                                <id><![CDATA[{image_id}]]></id>
                            </image>
                        </images>
                    </associations>
                </combination>
            </prestashop>
        """
        return body

    @staticmethod
    def prettify_xml(xml):
        """Convierte un ElementTree en un XML bien formateado sin &lt; ni &gt;"""
        reparsed = xml.replace("&lt;", "<").replace("&gt;", ">")
        return reparsed

    @staticmethod
    def report_error(data):
        print(f"❌ Error in {data['name']}:")
        print("Status code:", data["status_code"])
        print("Response:", data["response"])

    @staticmethod
    def transform_data_to_dict_name_id(data):
        data_dict = {}
        for value in data:
            data_dict[value['name']] = value['id']

        return {k.lower(): v for k, v in data_dict.items()}
    
    @staticmethod
    def body_product_option(attribute_name):
        if attribute_name == 'Color':
            is_color = 1
            color = "#AAB2BD"
        else:
            is_color = 1
            color = ""


        return f"""<?xml version="1.0" encoding="UTF-8"?>
            <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
                <product_option>
                    <is_color_group><![CDATA[{is_color}]]></is_color_group>
                    <color><![CDATA[{color}]]></color>
                    <group_type><![CDATA[select]]></group_type>
                    <name>
                        <language id="2"><![CDATA[{attribute_name}]]></language>
                    </name>
                    <public_name>
                        <language id="2"><![CDATA[{attribute_name}]]></language>
                    </public_name>
                </product_option>
            </prestashop>
        """

    @staticmethod
    def body_product_option_value(id_product_option, value):
        return f"""<?xml version="1.0" encoding="UTF-8"?>
            <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
                <product_option_value>
                    <id_attribute_group><![CDATA[{id_product_option}]]></id_attribute_group>
                    <name>
                        <language id="2"><![CDATA[{value}]]></language>
                    </name>
                </product_option_value>
            </prestashop>
        """