from .reference_value_set_extractor import ReferenceValueSetExtractor


class CountrySetExtractor(ReferenceValueSetExtractor):

    def _build_entry(self, element):
        entry = super()._build_entry(element)
        entry['iso2'] = element.attrib.get('ISO2')
        return entry
