TREASURY_ADDRESS_FIELDS = [
    'ADDRESS1',
    'ADDRESS2',
    'ADDRESS3',
]

TREASURY_FEATURE_TO_CSL_FIELD_DICT = {
    'Birthdate': 'dates_of_birth',
    'Place of Birth': 'places_of_birth',
    'Citizenship Country': 'citizenships',
    'Location': 'addresses'
}

COUNTRY_FEATURE_KEYS = frozenset([
    'Nationality of Registration'
])


def transform(entry):
    distinct_party = entry['distinct_party']
    profile_id = str(distinct_party['profile_id'])
    entry_type = distinct_party['party_type']
    remarks = distinct_party['comment']
    programs = []
    if 'programs' in entry['sanctions_measures']:
        programs = entry['sanctions_measures']['programs']

    aliases = distinct_party['aliases']
    name = __transform_name(aliases['Name'][0])

    alt_names = []
    if 'A.K.A.' in aliases:
        alt_names.extend([__transform_name(name_dict) for name_dict in aliases['A.K.A.']])

    if 'F.K.A.' in aliases:
        alt_names.extend([__transform_name(name_dict) for name_dict in aliases['F.K.A.']])

    ids = []
    if 'id_registrations' in distinct_party:
        ids.extend(__transform_ids(distinct_party['id_registrations']))

    transformed_entry = {
        'id': profile_id,
        'name': name,
        'alt_names': alt_names,
        'entity_number': profile_id,
        'type': entry_type,
        'remarks': remarks,
        'programs': programs,
        'ids': ids
    }

    features = distinct_party['features']
    for i in features:
        csl_key, feature_value = __transform_feature(i)
        if csl_key in transformed_entry:
            transformed_entry[csl_key].append(feature_value)
        else:
            transformed_entry[csl_key] = [feature_value]

    return transformed_entry


def __transform_name(name_dict):
    if 'Entity Name' in name_dict:
        return name_dict['Entity Name']
    else:
        name_parts = []
        if 'First Name' in name_dict: name_parts.append(name_dict['First Name'])
        if 'Last Name' in name_dict: name_parts.append(name_dict['Last Name'])

        return ' '.join(name_parts)


def __transform_ids(id_registrations):
    ids = []
    for id_reg in id_registrations:
        id_entry = {
            'type': id_reg['IdRegDocType'],
            'number': id_reg['IdRegNo'],
        }

        if 'Country' in id_reg:
            id_entry['country'] = id_reg['Country']

        ids.append(id_entry)

    return ids


def __transform_feature(feature):
    csl_key = None
    feature_value = None
    for k, v in feature.items():
        if k in TREASURY_FEATURE_TO_CSL_FIELD_DICT:
            csl_key = TREASURY_FEATURE_TO_CSL_FIELD_DICT[k]
            feature_value = __transform_location(v) if k == 'Location' else v

        else:
            csl_key = 'ids'
            feature_value = __build_ids_value_from_feature(k, v)

    return csl_key, feature_value


def __transform_location(location):
    address_lines = [location.get(field) for field in TREASURY_ADDRESS_FIELDS]
    city = location.get('CITY')
    state = location.get('STATE/PROVINCE')
    postal_code = location.get('POSTAL CODE')
    country = location.get('COUNTRY')
    address = [address_line for address_line in address_lines if address_line is not None]
    address_str = ', '.join(address) if address else None

    address_fields = {
        'address': address_str,
        'city': city,
        'state': state,
        'postal_code': postal_code,
        'country': country
    }

    return address_fields


def __build_ids_value_from_feature(k, v):
    id_entry = {'type': k}
    id_key = 'country' if k in COUNTRY_FEATURE_KEYS else 'number'
    id_entry[id_key] = v

    return id_entry
