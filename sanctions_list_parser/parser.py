import xml.etree.ElementTree as ElementTree

from . import xpath_finder as finder

LOCATION_FEATURE_TYPE_ID = 25


class Parser:
    def __init__(self, source):
        tree = ElementTree.parse(source)
        self.root = tree.getroot()
        self.sanctions_lists = self.__parse_sanctions_lists()
        self.party_sub_types = self.__parse_party_sub_types()
        self.party_types = self.__parse_party_types()
        self.feature_types = self.__parse_feature_types()
        self.detail_types = self.__parse_detail_types()
        self.countries = self.__parse_countries()
        self.sanctions_lists_by_list_id = {}

    def get_sanctions_list_by_name(self, name):
        normalized_name = name.lower().strip()
        return next(sanctions_list for sanctions_list in self.sanctions_lists.values() if
                    normalized_name in sanctions_list['name'].lower())

    def get_sanctions_entries_by_list_id(self, list_id):
        if list_id in self.sanctions_lists_by_list_id:
            sanctions_entries = self.sanctions_lists_by_list_id[list_id]
        else:
            sanctions_entries = self.__parse_sanctions_entries(list_id)
            self.sanctions_lists_by_list_id[list_id] = sanctions_entries

        return [entry for entry in sanctions_entries.values()]

    def __parse_sanctions_lists(self):
        parsed_sanctions_lists = {}
        for sanctions_list in finder.find_all_lists(self.root):
            list_id = int(sanctions_list.attrib['ID'])
            name = sanctions_list.text.strip()
            parsed_sanctions_lists[list_id] = {'id': list_id, 'name': name}

        return parsed_sanctions_lists

    def __parse_party_sub_types(self):
        party_sub_types = {}
        for party_sub_type in finder.find_all_party_sub_types(self.root):
            party_sub_type_id = int(party_sub_type.attrib['ID'])
            party_type_id = int(party_sub_type.attrib['PartyTypeID'])
            party_sub_type_text = party_sub_type.text.strip()
            party_sub_types[party_sub_type_id] = {
                'id': party_sub_type_id,
                'party_type_id': party_type_id,
                'name': party_sub_type_text
            }

        return party_sub_types

    def __parse_party_types(self):
        party_types = {}
        for party_type in finder.find_all_party_types(self.root):
            party_type_id = int(party_type.attrib['ID'])
            party_type_text = party_type.text.strip()
            party_types[party_type_id] = {
                'id': party_type_id,
                'type': party_type_text
            }

        return party_types

    def __parse_feature_types(self):
        feature_types = {}
        for feature_type in finder.find_all_feature_types(self.root):
            feature_type_id = int(feature_type.attrib['ID'])
            feature_type_text = feature_type.text.strip()
            feature_types[feature_type_id] = {
                'id': feature_type_id,
                'type': feature_type_text
            }

        return feature_types

    def __parse_detail_types(self):
        detail_types = {}
        for detail_type in finder.find_all_detail_types(self.root):
            detail_type_id = int(detail_type.attrib['ID'])
            detail_type_name = detail_type.text.strip()
            detail_types[detail_type_id] = {
                'id': detail_type_id,
                'type': detail_type_name
            }

        return detail_types

    def __parse_countries(self):
        country_values = {}
        for country in finder.find_all_countries(self.root):
            country_id = int(country.attrib['ID'])

            country_iso2 = None
            if 'ISO2' in country.attrib: country_iso2 = country.attrib['ISO2']
            country_name = country.text.strip()
            country_values[country_id] = {
                'id': country_id,
                'iso2': country_iso2,
                'name': country_name
            }

        return country_values

    def __parse_sanctions_entries(self, list_id):
        sanctions_entries = {}
        for entry in finder.find_all_sanctions_entries_by_list_id(self.root, list_id):
            entry_id = int(entry.attrib['ID'])
            programs = self.__parse_programs(entry)
            entry_fields = {
                'id': entry_id,
                'programs': programs
            }
            distinct_party_fields = self.__parse_distinct_party(self.root, entry)
            entry_fields.update(distinct_party_fields)

            sanctions_entries[entry_id] = entry_fields

        return sanctions_entries

    def __parse_programs(self, entry):
        sanctions_measures = finder.find_all_program_sanction_measures(entry)
        programs = []

        for sanctions_measure in sanctions_measures:
            comment = finder.find_comment(sanctions_measure)
            if comment is not None:
                program = comment.text.strip()
                programs.append(program)

        return programs

    def __parse_distinct_party(self, root, entry):
        distinct_party = finder.find_distinct_party(root, entry)
        remarks = self.__parse_remarks(distinct_party)
        distinct_party_fields = {
            'remarks': remarks
        }
        profile_fields = self.__parse_profile(root, distinct_party)
        distinct_party_fields.update(profile_fields)

        return distinct_party_fields

    def __parse_remarks(self, distinct_party):
        remarks = None
        comment = finder.find_comment(distinct_party)
        if comment is not None:
            remarks = comment.text.strip()
        return remarks

    def __parse_profile(self, root, distinct_party):
        profile = finder.find_profile(distinct_party)
        party_sub_type_id = int(profile.attrib['PartySubTypeID'])
        party_sub_type = self.party_sub_types[party_sub_type_id]
        party_type_id = party_sub_type['party_type_id']
        party_type = self.party_types[party_type_id]

        name = self.__parse_name(profile)
        alt_names = self.__parse_alt_names(profile)
        ids = self.__parse_features(root, profile, 13)

        addresses = self.__parse_version_locations(root, profile)

        profile_fields = {
            'name': name,
            'alt_names': alt_names,
            'type': party_type['type'],
            'ids': ids,
            'addresses': addresses
        }

        return profile_fields

    def __parse_name(self, profile):
        name_alias = finder.find_name_alias(profile)
        return self.__parse_alias(name_alias)

    def __parse_alt_names(self, profile):
        alt_name_aliases = finder.find_all_alt_name_aliases(profile)
        alt_names = []

        for alias in alt_name_aliases:
            alt_name = self.__parse_alias(alias)
            alt_names.append(alt_name)

        return alt_names

    def __parse_alias(self, alias):
        return finder.find_name_part_value(alias).text.strip()

    def __parse_features(self, root, profile, feature_type_id):
        features = [self.__parse_feature(root, feature) for feature in
                    finder.find_all_features(profile, feature_type_id)]

        return features

    def __parse_feature(self, root, feature):
        feature_type_id = int(feature.attrib['FeatureTypeID'])
        feature_type = self.feature_types[feature_type_id]

        feature_fields = {}

        if feature_type_id == 13:
            version_detail_fields = self.__parse_version_detail(feature)
            feature_fields = {
                'type': feature_type['type'],
                'number': version_detail_fields['value']
            }

        return feature_fields

    def __parse_version_detail(self, feature):
        version_detail = finder.find_version_detail(feature)
        version_detail_type_id = int(version_detail.attrib['DetailTypeID'])
        version_detail_type = self.detail_types[version_detail_type_id]
        value = version_detail.text.strip()

        version_detail_fields = {
            'type': version_detail_type['type'],
            'value': value
        }

        return version_detail_fields

    def __parse_version_locations(self, root, profile):
        addresses = [self.__parse_location(root, version_location) for version_location in
                     finder.find_all_version_locations(profile)]
        return addresses

    def __parse_location(self, root, version_location):
        location_id = int(version_location.attrib['LocationID'])
        location = finder.find_location(root, location_id)

        address1 = self.__parse_location_part_value(location, 1451)
        address2 = self.__parse_location_part_value(location, 1452)
        address3 = self.__parse_location_part_value(location, 1453)
        city = self.__parse_location_part_value(location, 1454)
        state = self.__parse_location_part_value(location, 1455)
        postal_code = self.__parse_location_part_value(location, 1456)
        country = self.__parse_location_country(location)

        address_lines = [address1, address2, address3]

        address = [address_line for address_line in address_lines if address_line is not None]

        address_fields = {
            'address': ', '.join(address),
            'city': city,
            'state': state,
            'postal_code': postal_code,
            'country': country
        }

        return address_fields

    def __parse_location_part_value(self, location, location_part_type_id):
        location_part_value = finder.find_location_part_value(location, location_part_type_id)
        if location_part_value is not None and location_part_value.text is not None:
            return location_part_value.text.strip()
        else:
            return None

    def __parse_location_country(self, location):
        location_country = finder.find_location_country(location)
        country_id = int(location_country.attrib['CountryID'])
        country = self.countries[country_id]

        return country['iso2']
