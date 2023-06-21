from . import xpath_finder as finder


def extract(parent):
    comment = None
    element = finder.find_comment(parent)
    if element is not None:
        comment = element.text.strip()
    return comment
