from . import comment_extractor
from . import features_extractor
from . import xpath_finder as finder


def extract(reference_dict, root, profile_id):
    distinct_party = finder.find_distinct_party(root, profile_id)
    profile = finder.find_profile(distinct_party, profile_id)
    identity = finder.find_identity(profile)

    comment = comment_extractor.extract(distinct_party)
    party_type = __extract_party_type(reference_dict, profile)
    id_registrations = __extract_id_registrations(reference_dict, root, identity)
    aliases = __extract_aliases(reference_dict, profile)
    features = features_extractor.extract(reference_dict, root, profile)
    return {
        'profile_id': profile_id,
        'comment': comment,
        'party_type': party_type,
        'id_registrations': id_registrations,
        'aliases': aliases,
        'features': features
    }


def __extract_party_type(reference_dict, profile):
    party_sub_type_id = int(profile.attrib['PartySubTypeID'])
    party_sub_type_reference_dict = reference_dict['PartySubType']
    party_type_id = party_sub_type_reference_dict[party_sub_type_id]['party_type_id']

    party_type_reference_dict = reference_dict['PartyType']
    return party_type_reference_dict[party_type_id]['value']


def __extract_id_registrations(reference_dict, root, identity):
    identity_id = identity.attrib['ID']
    country_reference_dict = reference_dict['Country']
    id_reg_doc_reference_dict = reference_dict['IDRegDocType']
    id_registration_list = []

    for id_reg_doc in finder.find_id_reg_documents(root, identity_id):
        id_reg_doc_type_id = int(id_reg_doc.attrib['IDRegDocTypeID'])
        id_reg_doc_type = id_reg_doc_reference_dict[id_reg_doc_type_id]['value']
        id_reg_no = finder.find_id_registration_no(id_reg_doc).text.strip()

        id_registration = {
            'IdRegDocType': id_reg_doc_type,
            'IdRegNo': id_reg_no,
        }

        if 'IssuedBy-CountryID' in id_reg_doc.attrib:
            country_id = int(id_reg_doc.attrib['IssuedBy-CountryID'])
            country = country_reference_dict[country_id]['iso2']
            id_registration['Country'] = country

        id_registration_list.append(id_registration)

    return id_registration_list


def __extract_aliases(reference_dict, profile):
    alias_type_dict = reference_dict['AliasType']
    alias_dict = {}
    for a in finder.find_aliases(profile):
        alias_type = alias_type_dict[int(a.attrib['AliasTypeID'])]['value']
        aliases = alias_dict[alias_type] if alias_type in alias_dict else []
        name_part_value_dict = __extract_name_part_value_dict(reference_dict, profile, a)
        aliases.append(name_part_value_dict)
        alias_dict[alias_type] = aliases

    return alias_dict


def __extract_name_part_value_dict(reference_dict, profile, alias):
    name_part_group_dict = __extract_name_part_group_part_type_dict(
        reference_dict['NamePartType'],
        profile
    )

    name_part_value_dict = {}
    for v in finder.find_latin_name_part_values(alias):
        name_part_group_id = int(v.attrib['NamePartGroupID'])
        name_part_type = name_part_group_dict[name_part_group_id]['name_part_type']
        name_part_text = v.text.strip()
        name_part_value_dict[name_part_type] = name_part_text

    return name_part_value_dict


def __extract_name_part_group_part_type_dict(name_part_type_reference_dict, profile):
    name_part_group_dict = {}
    for name_part_group in finder.find_name_part_groups(profile):
        name_part_group_id = int(name_part_group.attrib['ID'])
        name_part_type_id = int(name_part_group.attrib['NamePartTypeID'])
        name_part_type = name_part_type_reference_dict[name_part_type_id]['value']

        name_part_group_dict[name_part_group_id] = {
            'id': name_part_group_id,
            'name_part_type': name_part_type
        }

    return name_part_group_dict
