import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import traceback
from lxml import etree


class XmlNative:
    def __init__(self):
        self.root = None

    # -------------------------------
    # Soporta: xml.Tag = "ECF"
    # -------------------------------
    @property
    def Tag(self):
        return self.root.tag if self.root is not None else None

    @Tag.setter
    def Tag(self, value):
        if self.root is None:
            self.root = ET.Element(value)
        else:
            self.root.tag = value

    # -------------------------------
    # Utilidades internas
    # -------------------------------
    def _get_or_create_path(self, path: str):
        """
        Replica el comportamiento de Chilkat:
        - Si el root no existe, lo crea automáticamente
        - Soporta paths tipo: Encabezado|IdDoc|Item[0]
        """

        # 🔑 FIX CLAVE: crear root automáticamente
        if self.root is None:
            self.root = ET.Element("ECF")

        parts = path.split("|")
        current = self.root

        for part in parts:
            index = None

            if "[" in part and "]" in part:
                tag, idx = part[:-1].split("[")
                index = int(idx)
            else:
                tag = part

            # 🔑 current SIEMPRE debe ser iterable
            children = [c for c in list(current) if c.tag == tag]

            if index is not None:
                while len(children) <= index:
                    current.append(ET.Element(tag))
                    children = [c for c in list(current) if c.tag == tag]
                current = children[index]
            else:
                if children:
                    current = children[0]
                else:
                    new_elem = ET.Element(tag)
                    current.append(new_elem)
                    current = new_elem

        return current

    # -------------------------------
    # Reemplazo directo Chilkat
    # -------------------------------
    def UpdateChildContent(self, path: str, value):
        if value is None:
            return
        if self.root is None:
            self.root = ET.Element("ECF")
        elem = self._get_or_create_path(path)
        elem.text = str(value)

    def UpdateChildContentInt(self, path: str, value):
        if value is None:
            return
        elem = self._get_or_create_path(path)
        elem.text = str(int(value))

    # -------------------------------
    # Guardar XML (equivalente SaveXml)
    # -------------------------------
    def SaveXml(self, filename: str):
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        rough_string = ET.tostring(self.root, encoding="utf-8")
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8")

        with open(filename, "wb") as f:
            f.write(pretty_xml)

    def ToString(self, pretty=True):
        """
        Devuelve el XML como string (para print, logs o debug)
        """
        if self.root is None:
            return ""

        rough_string = ET.tostring(self.root, encoding="utf-8")

        if not pretty:
            return rough_string.decode("utf-8")

        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
