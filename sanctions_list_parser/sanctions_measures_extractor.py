from . import comment_extractor
from . import xpath_finder as finder


def extract(entry):
    sanctions_measures = finder.find_program_sanction_measures(entry)
    programs = []

    for sanctions_measure in sanctions_measures:
        comment = comment_extractor.extract(sanctions_measure)
        if comment is not None:
            programs.append(comment)

    return {'programs': programs}
