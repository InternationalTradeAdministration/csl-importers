from . import xpath_finder as finder


def extract(reference_dict, root, location_id):
    loc_part_type_reference_dict = reference_dict['LocPartType']
    location = finder.find_location(root, location_id)
    location_part_dict = {}

    location_country = __extract_location_country(reference_dict, location)
    if location_country is not None:
        location_part_dict['COUNTRY'] = location_country

    for location_part in finder.find_location_parts(location):
        loc_part_type_id = int(location_part.attrib['LocPartTypeID'])
        loc_part_type = loc_part_type_reference_dict[loc_part_type_id]['value']
        loc_part_value = __extract_location_part_value(location_part)
        location_part_dict[loc_part_type] = loc_part_value

    return location_part_dict


def __extract_location_country(reference_dict, location):
    country_reference_dict = reference_dict['Country']
    location_country = finder.find_location_country(location)
    country_iso2 = None
    if location_country is not None:
        country_id = int(location_country.attrib['CountryID'])
        country_iso2 = country_reference_dict[country_id]['iso2']

    return country_iso2


def __extract_location_part_value(location_part):
    location_part_value = finder.find_primary_location_part_value(location_part)
    return location_part_value.text.strip()


