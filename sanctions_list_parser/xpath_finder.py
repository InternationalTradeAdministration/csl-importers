NS = {'un': 'http://www.un.org/sanctions/1.0'}
LATIN_SCRIPT_ID = 215
PROGRAM_SANCTIONS_TYPE_ID = 1


def find_all_reference_values(root, reference_value_element_name):
    reference_value_sets = root.find('.//un:ReferenceValueSets', NS)
    return reference_value_sets.findall(f'.//un:{reference_value_element_name}', NS)


def find_sanctions_entries_by_list_id(root, list_id):
    return root.findall(f'.//un:SanctionsEntries/un:SanctionsEntry[@ListID="{list_id}"]', NS)


def find_distinct_party(root, profile_id):
    return root.find(f'.//un:DistinctParty[@FixedRef="{profile_id}"]', NS)


def find_profile(distinct_party, profile_id):
    return distinct_party.find(f'./un:Profile[@ID="{profile_id}"]', NS)


def find_identity(profile):
    return profile.find('./un:Identity', NS)


def find_id_reg_documents(root, identity_id):
    return root.findall(f'.//un:IDRegDocuments/un:IDRegDocument[@IdentityID="{identity_id}"]', NS)


def find_id_registration_no(id_reg_document):
    return id_reg_document.find('./un:IDRegistrationNo', NS)


def find_features(profile):
    return profile.findall('.//un:Feature', NS)


def find_aliases(profile):
    return profile.findall(f'.//un:Alias', NS)


def find_latin_name_part_values(alias):
    return alias.findall(f'.//un:NamePartValue[@ScriptID="{LATIN_SCRIPT_ID}"]', NS)


def find_name_part_groups(profile):
    return profile.findall('.//un:NamePartGroups//un:NamePartGroup', NS)


def find_program_sanction_measures(entry):
    return entry.findall(f'.//un:SanctionsMeasure[@SanctionsTypeID="{PROGRAM_SANCTIONS_TYPE_ID}"]', NS)


def find_comment(element):
    comment = element.find('./un:Comment', NS)
    if comment is not None and comment.text is not None:
        return comment
    else:
        return None


def find_version_detail(feature):
    return feature.find('.//un:VersionDetail', NS)


def find_version_location(feature):
    return feature.find('.//un:VersionLocation', NS)


def find_date_period(feature):
    return feature.find('.//un:DatePeriod', NS)


def find_date_point(boundary, start_or_from, date_period):
    return date_period.find(f'./un:{boundary}/un:{start_or_from}', NS)


def find_date_part(parent, date_part_name):
    return parent.find(f'./un:{date_part_name}', NS)


def find_location(root, location_id):
    return root.find(f'.//un:Location[@ID="{location_id}"]', NS)


def find_location_parts(location):
    return location.findall('.//un:LocationPart', NS)


def find_primary_location_part_value(location_part):
    return location_part.find('.//un:LocationPartValue[@Primary="true"]/un:Value', NS)


def find_location_country(location):
    return location.find('./un:LocationCountry', NS)
