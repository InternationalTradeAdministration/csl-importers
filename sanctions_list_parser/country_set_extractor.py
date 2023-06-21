from .reference_value_set_extractor import ReferenceValueSetExtractor


class CountrySetExtractor(ReferenceValueSetExtractor):

    def _build_entry(self, element):
        item = super()._build_entry(element)
        country_iso2 = None
        if 'ISO2' in element.attrib:
            country_iso2 = element.attrib['ISO2']
        item['iso2'] = country_iso2
        return item
