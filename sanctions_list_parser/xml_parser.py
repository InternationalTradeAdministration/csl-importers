import xml.etree.ElementTree as ElementTree


def get_root(source):
    tree = ElementTree.parse(source)
    return tree.getroot()
