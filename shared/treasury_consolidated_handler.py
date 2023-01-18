import xml.etree.ElementTree as ET

from . import citizenship, convert_date, name_extractor, nested_fields


NS = {'xmlns': 'http://tempuri.org/sdnList.xsd'}
ADDRESS_PATH = 'xmlns:addressList/xmlns:address'
ALT_NAMES_PATH = 'xmlns:akaList/xmlns:aka'
CITIZENSHIP_PATH = 'xmlns:citizenshipList/xmlns:citizenship/xmlns:country'
DOB_PATH = 'xmlns:dateOfBirthList/xmlns:dateOfBirthItem/xmlns:dateOfBirth'
POB_PATH = 'xmlns:placeOfBirthList/xmlns:placeOfBirthItem'
ID_PATH = 'xmlns:idList/xmlns:id'

NULL_FIELDS = [
    'call_sign', 'end_date', 'federal_register_notice',
    'gross_registered_tonnage', 'gross_tonnage',
    'license_policy', 'license_requirement',
    'nationalities', 'standard_order',
    'start_date', 'title', 'vessel_flag',
    'vessel_owner', 'vessel_type'
]


def entries(response):
    tree = ET.parse(response)
    root = tree.getroot()
    return root.findall('xmlns:sdnEntry', NS)


def extract(entry):
    doc = {}
    programs = entry.find('xmlns:programList', NS)
    doc['programs'] = list(map(lambda program: program.text, programs))

    ids = entry.findall(ID_PATH, NS)
    doc['ids'] = nested_fields.get_ids(ids)

    doc['entity_number'] = entry.find('xmlns:uid', NS).text.strip()
    doc['id'] = entry.find('xmlns:uid', NS).text.strip()
    doc['name'] = name_extractor.get_name(entry)

    remarks = entry.find('xmlns:remarks', NS)
    doc['remarks'] = remarks.text if remarks is not None else None

    doc['type'] = entry.find('xmlns:sdnType', NS).text.strip()

    addresses = entry.findall(ADDRESS_PATH, NS)
    doc['addresses'] = nested_fields.get_multiline_addresses(addresses)

    alt_names = entry.findall(ALT_NAMES_PATH, NS)
    doc['alt_names'] = name_extractor.get_alt_names(alt_names)

    citizenships = entry.findall(CITIZENSHIP_PATH, NS)
    doc['citizenships'] = citizenship.get_citizenship(citizenships)

    dob = entry.find(DOB_PATH, NS)
    doc['dates_of_birth'] = convert_date.parse_date(dob.text) if dob is not None else None

    pob = entry.findall(POB_PATH, NS)
    doc['places_of_birth'] = nested_fields.get_places_of_birth(pob) if pob is not None else None

    for f in NULL_FIELDS:
        doc[f] = None

    return doc


def flatten_list(doc):
    doc['addresses'] = nested_fields.make_flat_address(doc['addresses'])
    doc['alt_names'] = '; '.join(doc['alt_names'])
    doc['programs'] = '; '.join(doc['programs'])
    doc['places_of_birth'] = '; '.join(doc['places_of_birth'])
    doc['_id'] = doc['id']
    del doc['id']
    id_list = []
    for d in doc['ids']:
        id_list.append(", ".join([v for v in d.values() if v]))
    doc['ids'] = "; ".join(id_list)
    return doc
