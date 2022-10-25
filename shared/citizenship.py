from . import country_code


def get_citizenship(citizenships):
    country = [
        country_code.get_country_code(child.text.strip())
        for child in citizenships
        if child.text and len(child.text.strip()) > 0
    ]
    return country if country else None
