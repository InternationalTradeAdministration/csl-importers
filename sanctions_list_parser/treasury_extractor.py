from . import distinct_party_extractor
from . import reference_dict_builder
from . import sanctions_measures_extractor
from . import xml_parser
from . import xpath_finder as finder


class TreasuryExtractor:

    def __init__(self, source):
        self._root = xml_parser.get_root(source)
        self._reference_dict = reference_dict_builder.build(self._root)

    def extract_sanctions_entries(self, list_id):
        entries = {}
        for e in finder.find_sanctions_entries_by_list_id(self._root, list_id):
            entry_id = int(e.attrib['ID'])
            sanctions_measures = sanctions_measures_extractor.extract(e)
            distinct_party = distinct_party_extractor.extract(
                self._reference_dict, self._root, int(e.attrib['ProfileID']))

            entry = {
                'id': entry_id,
                'sanctions_measures': sanctions_measures,
                'distinct_party': distinct_party
            }
            entries[entry_id] = entry

        return entries
