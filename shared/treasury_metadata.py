SOURCES_DICT = {
    'cap': {
        'list_id': 91763,
        'source': 'Capta List (CAP) - Treasury Department',
        'list_url': 'https://www.treasury.gov/ofac/downloads/sanctions/1.0/cons_advanced.xml',
        'list_information_url': 'https://ofac.treasury.gov/consolidated-sanctions-list-non-sdn-lists/list-of-foreign-financial-institutions-subject-to-correspondent-account-or-payable-through-account-sanctions-capta-list'
    },
    'cmic': {
        'list_id': 92052,
        'source': 'Non-SDN Chinese Military-Industrial Complex Companies List (CMIC) - Treasury Department',
        'list_url': 'https://www.treasury.gov/ofac/downloads/sanctions/1.0/cons_advanced.xml',
        'list_information_url': 'https://ofac.treasury.gov/consolidated-sanctions-list/ns-cmic-list'
    },
    'mbs': {
        'list_id': 91868,
        'source': 'Non-SDN Menu-Based Sanctions List (NS-MBS List) - Treasury Department',
        'list_url': 'https://www.treasury.gov/ofac/downloads/sanctions/1.0/cons_advanced.xml',
        'list_information_url': 'https://ofac.treasury.gov/consolidated-sanctions-list-non-sdn-lists/non-sdn-menu-based-sanctions-list-ns-mbs-list'
    },
    'plc': {
        'list_id': 91243,
        'source': 'Palestinian Legislative Council List (PLC) - Treasury Department',
        'list_url': 'https://www.treasury.gov/ofac/downloads/sanctions/1.0/cons_advanced.xml',
        'list_information_url': 'https://ofac.treasury.gov/consolidated-sanctions-list/non-sdn-palestinian-legislative-council-ns-plc-list'
    },
}

def get_treasury_metadata(source_abbr):
    return SOURCES_DICT[source_abbr]
