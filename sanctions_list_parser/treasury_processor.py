from . import csl_transformer
from .treasury_extractor import TreasuryExtractor


class TreasuryProcessor:

    def __init__(self, source):
        self.__extractor = TreasuryExtractor(source)

    def get_sanctions_entries(self, list_id):
        entries = self.__extractor.extract_sanctions_entries(list_id)
        return [csl_transformer.transform(entry) for entry in entries.values()]
