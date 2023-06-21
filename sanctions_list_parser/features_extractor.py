import datetime

from . import location_extractor
from . import xpath_finder as finder


def extract(reference_dict, root, profile):
    features_list = []

    for f in finder.find_features(profile):
        version_detail = finder.find_version_detail(f)
        version_location = finder.find_version_location(f)
        feature_value = None
        if version_detail is not None:
            feature_value = __extract_feature_with_version_detail(reference_dict, root, f, version_detail, version_location)
        elif version_location is not None:
            feature_value = __extract_feature_with_version_location(reference_dict, root, version_location)

        if feature_value is not None:
            feature_type = __get_feature_type(reference_dict, f)
            features_list.append({feature_type: feature_value})

    return features_list


def __extract_feature_with_version_detail(reference_dict, root, feature, version_detail, version_location):
    detail_type = __get_detail_type(reference_dict, version_detail)
    feature_value = None
    if detail_type == 'DATE':
        feature_value = __extract_date(feature)
    elif detail_type == 'LOOKUP':
        feature_value = __extract_version_detail_lookup(
            reference_dict['DetailReference'],
            version_detail
        )
    elif detail_type == 'TEXT':
        feature_value = __extract_version_detail_text(version_detail)
    elif detail_type == 'COUNTRY':
        feature_value = __extract_country(reference_dict, root, version_location)

    return feature_value


def __extract_date(feature):
    date_period = finder.find_date_period(feature)
    return __extract_date_period(date_period)


def __extract_date_period(date_period):
    start_from = __extract_date_point(finder.find_date_point('Start', 'From', date_period))
    start_to = __extract_date_point(finder.find_date_point('Start', 'To', date_period))
    end_from = __extract_date_point(finder.find_date_point('End', 'From', date_period))
    end_to = __extract_date_point(finder.find_date_point('End', 'To', date_period))

    if len({start_from, start_to, end_from, end_to}) == 1:
        return start_from.strftime('%Y-%m-%d')
    elif __is_same_year_range(start_from, start_to, end_from, end_to):
        return str(start_from.year)


def __extract_date_point(parent):
    year = finder.find_date_part(parent, 'Year').text.strip()
    month = finder.find_date_part(parent, 'Month').text.strip()
    day = finder.find_date_part(parent, 'Day').text.strip()
    return datetime.date(int(year), int(month), int(day))


def __is_same_year_range(start_from, start_to, end_from, end_to):
    return all([
        start_from == start_to,
        end_from == end_to,
        start_from.year == end_from.year,
        start_from.month == 1,
        start_from.day == 1,
        end_from.month == 12,
        end_from.day == 31
    ])


def __extract_feature_with_version_location(reference_dict, root, version_location):
    location_id = int(version_location.attrib['LocationID'])
    location_dict = location_extractor.extract(reference_dict, root, location_id)
    return location_dict if location_dict else None


def __get_feature_type(reference_dict, feature):
    feature_type_id = int(feature.attrib['FeatureTypeID'])
    return reference_dict['FeatureType'][feature_type_id]['value']


def __get_detail_type(reference_dict, version_detail):
    detail_type_id = int(version_detail.attrib['DetailTypeID'])
    return reference_dict['DetailType'][detail_type_id]['value']


def __extract_version_detail_lookup(detail_reference_dict, version_detail):
    detail_reference_id = int(version_detail.attrib['DetailReferenceID'])
    return detail_reference_dict[detail_reference_id]['value']


def __extract_version_detail_text(version_detail):
    return version_detail.text.strip()


def __extract_country(reference_dict, root, version_location):
    location_id = int(version_location.attrib['LocationID'])
    location_dict = location_extractor.extract(reference_dict, root, location_id)
    country = location_dict['Unknown']
    reverse_country_reference_dict = reference_dict['ReverseCountry']
    country_iso2 = reverse_country_reference_dict[country]['iso2']
    return country_iso2
