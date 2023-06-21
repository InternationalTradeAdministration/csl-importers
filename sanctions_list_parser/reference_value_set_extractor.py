from . import xpath_finder as finder


class ReferenceValueSetExtractor:
    _key_field_name = 'id'

    def __init__(self, root, element_name):
        self.id_to_entry_dict = {}
        cls = self.__class__
        for e in finder.find_all_reference_values(root, element_name):
            entry = self._build_entry(e)
            self.id_to_entry_dict[entry[cls._key_field_name]] = entry

    def _build_entry(self, element):
        element_id = int(element.attrib['ID'])
        element_text = element.text.strip()

        return {
            'id': element_id,
            'value': element_text
        }
