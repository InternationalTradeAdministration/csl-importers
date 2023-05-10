NS = {'un': 'http://www.un.org/sanctions/1.0'}
NAME_ALIAS_TYPE_ID = 1403
PROGRAM_SANCTIONS_TYPE_ID = 1


def find_all_lists(root):
    return root.findall('.//un:ListValues/un:List', NS)


def find_all_party_sub_types(root):
    return root.findall('.//un:PartySubTypeValues/un:PartySubType', NS)


def find_all_party_types(root):
    return root.findall('.//un:PartyTypeValues/un:PartyType', NS)


def find_all_feature_types(root):
    return root.findall('.//un:FeatureTypeValues/un:FeatureType', NS)


def find_all_detail_types(root):
    return root.findall('.//un:DetailTypeValues/un:DetailType', NS)


def find_all_countries(root):
    return root.findall('.//un:CountryValues/un:Country', NS)


def find_all_sanctions_entries_by_list_id(root, list_id):
    return root.findall(f'.//un:SanctionsEntries/un:SanctionsEntry[@ListID="{list_id}"]', NS)


def find_distinct_party(root, entry):
    profile_id = int(entry.attrib['ProfileID'])
    return root.find(f'.//un:DistinctParty[@FixedRef="{profile_id}"]', NS)


def find_profile(distinct_party):
    return distinct_party.find('un:Profile', NS)


def find_all_features(profile, feature_type_id):
    features = profile.findall(f'un:Feature[@FeatureTypeID="{feature_type_id}"]', NS)
    return features


def find_name_alias(profile):
    paths = [
        'un:Identity',
        f'un:Alias[@AliasTypeID="{NAME_ALIAS_TYPE_ID}"]'
    ]
    return profile.find('/'.join(paths), NS)


def find_all_alt_name_aliases(profile):
    paths = [
        'un:Identity',
        'un:Alias'
    ]
    aliases = profile.findall('/'.join(paths), NS)
    return [alias for alias in aliases if int(alias.attrib['AliasTypeID']) != NAME_ALIAS_TYPE_ID]


def find_name_part_value(alias):
    return alias.find('.//un:NamePartValue', NS)


def find_all_program_sanction_measures(entry):
    return entry.findall(f'.//un:SanctionsMeasure[@SanctionsTypeID="{PROGRAM_SANCTIONS_TYPE_ID}"]', NS)


def find_comment(element):
    comment = element.find('.//un:Comment', NS)
    if comment is not None and comment.text is not None:
        return comment
    else:
        return None


def find_version_detail(feature):
    return feature.find('.//un:VersionDetail', NS)


def find_all_version_locations(profile):
    return profile.findall('.//un:VersionLocation', NS)


def find_location(root, location_id):
    return root.find(f'.//un:Location[@ID="{location_id}"]', NS)


def find_location_part_value(location, location_part_type_id):
    paths = [
        f'.//un:LocationPart[@LocPartTypeID="{location_part_type_id}"]',
        'un:Value'
    ]
    return location.find('//'.join(paths), NS)


def find_location_country(location):
    return location.find('un:LocationCountry', NS)
