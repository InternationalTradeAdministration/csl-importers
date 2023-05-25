import csv
import json
import hashlib
import logging
import os

from azure.storage.blob import BlobServiceClient, ContentSettings
from io import StringIO
from shared import convert_date, csl_meta, country_code, output, request

connection_string = os.environ["CONNECTION_STRING"]
csl_container = os.environ["CSL_CONTAINER"]
source_abbr = 'el'


def main():
    url = 'https://www.bis.doc.gov/index.php/documents/consolidated-entity-list/1072-el-2/file'
    source_list_url = 'https://www.bis.doc.gov/index.php/policy-guidance/lists-of-parties-of-concern/entity-list'
    source_information_url = 'https://www.bis.doc.gov/index.php/policy-guidance/lists-of-parties-of-concern/entity-list'
    source_name = 'Entity List (EL) - Bureau of Industry and Security'
    expected_headers = frozenset({
        'Source List', 'Entity Number', 'SDN Type',
        'Programs', 'Name', 'Title', 'Address', 'City',
        'State/Province', 'Postal Code', 'Country',
        'Federal Register Notice', 'Effective Date',
        'Date Lifted/Waived/Expired', 'Standard Order',
        'License Requirement', 'License Policy', 'Call Sign',
        'Vessel Type', 'Gross Tonnage', 'Gross Register Tonnage',
        'Vessel Flag', 'Vessel Owner', 'Remarks/Notes',
        'Address Number', 'Address Remarks', 'Alternate Number',
        'Alternate Type', 'Alternate Name', 'Alternate Remarks', 'Web Link'
    })

    logging.info('Checking last updated')
    last_modified = csl_meta.get_meta_url_last_modified(source_abbr)
    response = request.urlopen_with_user_agent(url)
    latest_modified = response.info()['Last-Modified']
    if last_modified == latest_modified:
        logging.info('No new data. Skipping processing.')
        return 0

    logging.info('Requesting data file')
    lines = [line.decode('utf-8-sig') for line in response.readlines()]
    csvfile = csv.DictReader(lines)
    source_csv_fields = list(filter(None, csvfile.fieldnames))
    logging.info('Checking header')
    if not expected_headers.issubset(set(source_csv_fields)):
        logging.info(f'fields not in source {expected_headers.difference(source_csv_fields)}')
        logging.info(f'new fields in source {set(source_csv_fields).difference(expected_headers)}')
        raise ValueError("Actual headers differ from expected headers")

    logging.info('Processing data')
    csv_output = StringIO()
    tsv_output = StringIO()
    json_output = StringIO()
    csv_writer = csv.DictWriter(csv_output, fieldnames=output.output_fields, dialect='unix')
    tsv_writer = csv.DictWriter(tsv_output, fieldnames=output.output_fields, dialect='unix', delimiter='\t')
    csv_writer.writeheader()
    tsv_writer.writeheader()
    doc_list = []
    seen = {}
    address_dict = {}
    for row in csvfile:
        key = row['Name'].lower().strip() + row['Federal Register Notice'].lower().strip()
        h = hashlib.sha224(key.encode()).hexdigest()
        if h in seen.keys():
            country = row['Country'].strip()
            cc = country_code.get_country_code(country)
            new_address = create_combined_address(row)
            new_address.append(cc)
            address = ', '.join(new_address)
            seen[h]['flat_address'] = f"{seen[h]['flat_address']}; {address}"
            additional_address = {
                'address': row['Address'],
                'city': row['City'],
                'state': row['State/Province'],
                'postal_code': row['Postal Code'],
                'country': cc
            }
            address_dict[h].append(additional_address)
        else:
            country = row['Country'].strip()
            cc = country_code.get_country_code(country)
            flat_addr = create_combined_address(row)
            flat_addr.append(cc)
            address = ', '.join(flat_addr)
            row['flat_address'] = address
            seen[h] = row
            address_dict[h] = [{
                'address': row['Address'],
                'city': row['City'],
                'state': row['State/Province'],
                'postal_code': row['Postal Code'],
                'country': cc
            }]

    for key, value in seen.items():
        str_date = value['Effective Date'].split(';')[0]
        str_date = str_date.split(',')[0]
        str_date = str_date.split(':')[0]
        start_date = convert_date.parse_american_date(str_date)
        doc = {
            '_id': key,
            'source': source_name,
            'name': value['Name'],
            'addresses': value['flat_address'],
            'federal_register_notice': value['Federal Register Notice'],
            'start_date': start_date if start_date else None,
            'standard_order': value['Standard Order'],
            'license_policy': value['License Policy'],
            'license_requirement': value['License Requirement'],
            'call_sign': value['Call Sign'],
            'vessel_type': value['Vessel Type'],
            'gross_tonnage': value['Gross Tonnage'],
            'gross_registered_tonnage': value['Gross Register Tonnage'],
            'vessel_flag': value['Vessel Flag'],
            'vessel_owner': value['Vessel Owner'],
            'remarks': value['Remarks/Notes'],
            'source_list_url': source_list_url,
            'alt_names': value['Alternate Name'],
            'source_information_url': source_information_url,
        }
        csv_writer.writerow(doc)
        tsv_writer.writerow(doc)
        doc['id'] = doc['_id']
        del doc['_id']
        doc['addresses'] = [addr for addr in address_dict[key]]
        doc['title'] = None
        doc['alt_names'] = doc['alt_names'].replace("; and", ";")
        doc['alt_names'] = doc['alt_names'].split('; ') if doc['alt_names'] else None
        doc['standard_order'] = None
        doc_list.append(doc)

    json.dump(doc_list, json_output)
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    logging.info('Write csv file')
    content_setting = ContentSettings(content_type='text/csv')
    blob_client = blob_service_client.get_blob_client(container=csl_container, blob=f"{source_abbr}.csv")
    blob_client.upload_blob(csv_output.getvalue(), overwrite=True, content_settings=content_setting)
    csv_output.close()
    logging.info('Write tsv file')
    content_setting = ContentSettings(content_type='text/tsv')
    blob_client = blob_service_client.get_blob_client(container=csl_container, blob=f"{source_abbr}.tsv")
    blob_client.upload_blob(tsv_output.getvalue(), overwrite=True, content_settings=content_setting)
    tsv_output.close()
    logging.info('Write json file')
    content_setting = ContentSettings(content_type='application/json')
    blob_client = blob_service_client.get_blob_client(container=csl_container, blob=f"{source_abbr}.json")
    blob_client.upload_blob(json_output.getvalue(), overwrite=True, content_settings=content_setting)
    json_output.close()
    logging.info('Write last modified file')
    content_setting = ContentSettings(content_type='text/plain')
    blob_client = blob_service_client.get_blob_client(container=csl_container, blob=f"{source_abbr}_meta.txt")
    blob_client.upload_blob(latest_modified, overwrite=True, content_settings=content_setting)
    json_output.close()


def create_combined_address(row):
    addr_parts = [
        row['Address'], row['City'], row['State/Province'], row['Postal Code']
    ]
    combined_address = [part for part in addr_parts if part]
    return combined_address
