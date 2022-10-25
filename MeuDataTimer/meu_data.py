import csv
import json
import logging
import os
import uuid

import urllib.request

from azure.storage.blob import BlobServiceClient, ContentSettings
from io import StringIO
from shared import convert_date, output

connection_string = os.environ["CONNECTION_STRING"]
csl_container = os.environ["CSL_CONTAINER"]
meu_meta_url = os.environ['MEU_META_URL']
source_abbr = 'meu'


def main():
    url = 'https://www.bis.doc.gov/meu/meu.csv'
    source_list_url = 'https://www.bis.doc.gov/index.php/policy-guidance/lists-of-parties-of-concern'
    source_name = 'Military End User (MEU) List - Bureau of Industry and Security'
    expected_headers = frozenset({
        'Source List', 'Entity Number', 'SDN Type',
        'Programs', 'Name', 'Title', 'Address',
        'City', 'State/Province', 'Postal Code', 'Country',
        'Federal Register Notice', 'Effective Date',
        'Date Lifted/Waived/Expired', 'Standard Order', 'License Requirement',
        'License Policy', 'Call Sign', 'Vessel Type', 'Gross Tonnage',
        'Gross Register Tonnage', 'Vessel Flag', 'Vessel Owner',
        'Remarks/Notes', 'Address Number', 'Address Remarks',
        'Alternate Number', 'Alternate Type', 'Alternate Name',
        'Alternate Remarks', 'Web Link'
    })

    logging.info('Checking last updated')
    last_modified = urllib.request.urlopen(meu_meta_url).read().decode('utf-8').strip()
    response = urllib.request.urlopen(url)
    latest_modified = response.info()['Last-Modified']
    if last_modified == latest_modified:
        logging.info('No new data. Skipping processing.')
        return 0

    logging.info('Requesting data file')
    lines = [line.decode('ISO-8859-1') for line in response.readlines()]
    csvfile = csv.DictReader(lines, delimiter=",", quotechar='"')
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
    for row in csvfile:
        id = uuid.uuid4().hex
        address = create_combined_address(row)
        start_date = convert_date.parse_american_date(row['Effective Date'])
        doc = {
                '_id': id,
                'source': source_name,
                'name': row['Name'],
                'alt_names': row['Alternate Name'],
                'addresses': address,
                'federal_register_notice': row['Federal Register Notice'],
                'start_date': start_date if start_date else None,
                'license_requirement': row['License Requirement'],
                'license_policy': row['License Policy'],
                'source_list_url': source_list_url,
                'source_information_url': source_list_url,
                'standard_order': row['Standard Order'],
        }
        csv_writer.writerow(doc)
        tsv_writer.writerow(doc)
        doc['id'] = doc['_id']
        del doc['_id']
        del doc['addresses']
        doc['addresses'] = [{
            'address': row['Address'],
            'city': row['City'],
            'state': row['State/Province'],
            'postal_code': row['Postal Code'],
            'country': 'CN'
        }]
        doc['title'] = None
        doc['alt_names'] = [] if doc['alt_names'] == "" else [doc['alt_names']]
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
        row['Address'], row['City'], row['State/Province'],
        row['Postal Code'], row['Country']
    ]
    combined_address = [part for part in addr_parts if part]
    combined_address.append('CN')
    return ', '.join(combined_address)
