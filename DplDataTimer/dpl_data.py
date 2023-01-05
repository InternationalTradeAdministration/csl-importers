import csv
import json
import hashlib
import logging
import os

import urllib.request

from azure.storage.blob import BlobServiceClient, ContentSettings
from io import StringIO
from shared import convert_date, csl_meta, output

connection_string = os.environ['CONNECTION_STRING']
csl_container = os.environ['CSL_CONTAINER']
source_abbr = 'dpl'


def main():
    url = 'https://www.bis.doc.gov/dpl/dpl.txt'
    source_list_url = 'https://www.bis.doc.gov/index.php/the-denied-persons-list'
    source_information_url = 'https://www.bis.doc.gov/index.php/policy-guidance/lists-of-parties-of-concern/denied-persons-list'
    source_name = 'Denied Persons List (DPL) - Bureau of Industry and Security'
    expected_headers = frozenset({
        'Name', 'Street_Address', 'City', 'State', 'Country', 'Postal_Code',
        'Effective_Date', 'Expiration_Date', 'Standard_Order', 'Last_Update',
        'Action', 'FR_Citation'
    })

    logging.info('Checking last updated')
    last_modified = csl_meta.get_meta_url_last_modified(source_abbr)
    response = urllib.request.urlopen(url)
    latest_modified = response.info()['Last-Modified']
    if last_modified == latest_modified:
        logging.info('No new data. Skipping processing.')
        return 0

    logging.info('Processing data file')
    lines = [line.decode('utf-8') for line in response.readlines()]
    csvfile = csv.DictReader(lines, delimiter="\t", quotechar='"')
    source_csv_fields = csvfile.fieldnames

    logging.info('Checking header')
    if not set(source_csv_fields) == (expected_headers):
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
        key = row['Name'].lower().strip() + row['FR_Citation'].lower().strip()
        h = hashlib.sha224(key.encode()).hexdigest()
        if h in seen.keys():
            new_address = create_combined_address(row)
            seen[h]['flat_address'] = f"{seen[h]['flat_address']}; {new_address}"
            additional_address = {
                'address': row['Street_Address'],
                'city': row['City'],
                'state': row['State'],
                'postal_code': row['Postal_Code'],
                'country': row['Country']
            }
            address_dict[h].append(additional_address)
        else:
            row['flat_address'] = create_combined_address(row)
            seen[h] = row
            address_dict[h] = [{
                'address': row['Street_Address'],
                'city': row['City'],
                'state': row['State'],
                'postal_code': row['Postal_Code'],
                'country': row['Country']
            }]

    for key, value in seen.items():
        start_date = convert_date.parse_american_date(value['Effective_Date'])
        end_date = convert_date.parse_american_date(value['Expiration_Date'])
        doc = {
            '_id': key,
            'source': source_name,
            'name': value['Name'],
            'addresses': value['flat_address'],
            'federal_register_notice': value['FR_Citation'],
            'start_date': start_date if start_date else None,
            'end_date': end_date if end_date else None,
            'standard_order': value['Standard_Order'],
            'remarks': value['Action'],
            'source_list_url': source_list_url,
            'source_information_url': source_information_url,
        }
        csv_writer.writerow(doc)
        tsv_writer.writerow(doc)
        doc['id'] = doc['_id']
        del doc['_id']
        doc['addresses'] = [addr for addr in address_dict[key]]
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
        row['Street_Address'], row['City'], row['State'],
        row['Postal_Code'], row['Country']
    ]
    combined_address = [part for part in addr_parts if part]
    return ', '.join(combined_address)
