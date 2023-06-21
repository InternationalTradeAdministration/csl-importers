from .reference_value_set_extractor import ReferenceValueSetExtractor


class PartySubTypeExtractor(ReferenceValueSetExtractor):

    def _build_entry(self, element):
        item = super()._build_entry(element)
        party_type_id = int(element.attrib['PartyTypeID'])
        item['party_type_id'] = party_type_id
        return item
