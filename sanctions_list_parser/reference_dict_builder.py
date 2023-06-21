from .country_set_extractor import CountrySetExtractor
from .party_sub_type_extractor import PartySubTypeExtractor
from .reference_value_set_extractor import ReferenceValueSetExtractor
from .reverse_country_set_extractor import ReverseCountrySetExtractor


def build(root):
    return {
        'AliasType': ReferenceValueSetExtractor(root, 'AliasType').id_to_entry_dict,
        'Country': CountrySetExtractor(root, 'Country').id_to_entry_dict,
        'DetailReference': ReferenceValueSetExtractor(root, 'DetailReference').id_to_entry_dict,
        'DetailType': ReferenceValueSetExtractor(root, 'DetailType').id_to_entry_dict,
        'FeatureType': ReferenceValueSetExtractor(root, 'FeatureType').id_to_entry_dict,
        'IDRegDocType': ReferenceValueSetExtractor(root, 'IDRegDocType').id_to_entry_dict,
        'List': ReferenceValueSetExtractor(root, 'List').id_to_entry_dict,
        'LocPartType': ReferenceValueSetExtractor(root, 'LocPartType').id_to_entry_dict,
        'NamePartType': ReferenceValueSetExtractor(root, 'NamePartType').id_to_entry_dict,
        'PartySubType': PartySubTypeExtractor(root, 'PartySubType').id_to_entry_dict,
        'PartyType': ReferenceValueSetExtractor(root, 'PartyType').id_to_entry_dict,
        'ReverseCountry': ReverseCountrySetExtractor(root, 'Country').id_to_entry_dict,
        'SanctionsProgram': ReferenceValueSetExtractor(root, 'SanctionsProgram').id_to_entry_dict
    }
