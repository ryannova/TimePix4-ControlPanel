import base64
from xml.dom import minidom
from xmlrpc.client import Boolean
import numpy as np
from timepix_image import TimepixImageControl

class timepix_xml:
    def __init__(self) -> None:
        self.root = minidom.Document()
        self.image_encoding = "base64"
        self.string_encoding = "utf-8"
    
    def _create_image_element(self, img : np.array) -> minidom.Element:
        image : minidom.Element = self.root.createElement("image")
        image.setAttribute("image_encoding", self.image_encoding)
        image.setAttribute("string_encoding", self.string_encoding)
        image.appendChild(self.root.createTextNode(base64.b64encode(img).decode("utf-8")))
        return image

    def add_images_element(self, imgs : np.array):
        images : minidom.Element = self.root.createElement("images")
        index = 0
        for img in imgs:
            image = self._create_image_element(img)
            image.setAttribute("index", str(index))
            index += 1
            images.appendChild(image)
        images.setAttribute("number_of_images", str(index))
        self.root.appendChild(images)
        return images

    def write_to_file(self, filename : str, prettyxml : bool = False):
        if prettyxml:
            xml_str = self.root.toprettyxml(indent="\t")
        else:
            xml_str = self.root.toxml()
        with open(filename, "w") as f:
            f.write(xml_str)