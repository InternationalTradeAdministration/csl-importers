NON_SDN_SOURCE_URL = 'https://sanctionslistservice.ofac.treas.gov/api/publicationpreview/exports/cons_advanced.xml'
NON_SDN_LIST_URL = 'https://sanctionslist.ofac.treas.gov/Home/ConsolidatedList'

SOURCES_DICT = {
    'cap': {
        'list_id': 91763,
        'source': 'Capta List (CAP) - Treasury Department',
        'source_url': NON_SDN_SOURCE_URL,
        'list_url': NON_SDN_LIST_URL,
        'list_information_url': 'https://ofac.treasury.gov/other-ofac-sanctions-lists'
    },
    'cmic': {
        'list_id': 92052,
        'source': 'Non-SDN Chinese Military-Industrial Complex Companies List (CMIC) - Treasury Department',
        'source_url': NON_SDN_SOURCE_URL,
        'list_url': NON_SDN_LIST_URL,
        'list_information_url': 'https://ofac.treasury.gov/other-ofac-sanctions-lists'
    },
    'fse': {
        'list_id': 91469,
        'source': 'Foreign Sanctions Evaders (FSE) - Treasury Department',
        'source_url': NON_SDN_SOURCE_URL,
        'list_url': NON_SDN_LIST_URL,
        'list_information_url': 'https://ofac.treasury.gov/other-ofac-sanctions-lists'
    },
    'mbs': {
        'list_id': 91868,
        'source': 'Non-SDN Menu-Based Sanctions List (NS-MBS List) - Treasury Department',
        'source_url': NON_SDN_SOURCE_URL,
        'list_url': NON_SDN_LIST_URL,
        'list_information_url': 'https://ofac.treasury.gov/other-ofac-sanctions-lists'
    },
    'plc': {
        'list_id': 91243,
        'source': 'Palestinian Legislative Council List (PLC) - Treasury Department',
        'source_url': NON_SDN_SOURCE_URL,
        'list_url': NON_SDN_LIST_URL,
        'list_information_url': 'https://ofac.treasury.gov/other-ofac-sanctions-lists'
    },
    'ssi': {
        'list_id': 91507,
        'source': 'Sectoral Sanctions Identifications List (SSI) - Treasury Department',
        'source_url': NON_SDN_SOURCE_URL,
        'list_url': NON_SDN_LIST_URL,
        'list_information_url': 'https://ofac.treasury.gov/other-ofac-sanctions-lists'
    }
}

def get_treasury_metadata(source_abbr):
    return SOURCES_DICT[source_abbr]
