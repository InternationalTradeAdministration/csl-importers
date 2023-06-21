from .country_set_extractor import CountrySetExtractor


class ReverseCountrySetExtractor(CountrySetExtractor):
    _key_field_name = 'value'
