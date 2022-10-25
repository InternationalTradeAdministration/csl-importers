import csv
import json
import hashlib
import logging
import os

import urllib.request

from azure.storage.blob import BlobServiceClient, ContentSettings
from io import StringIO
from shared import convert_date, country_code, output

connection_string = os.environ["CONNECTION_STRING"]
csl_container = os.environ["CSL_CONTAINER"]
isn_meta_url = os.environ['ISN_META_URL']
source_abbr = 'isn'


def main():
    url = 'https://csldata.blob.core.windows.net/csltempdata/sanctions.csv'
    source_information_url = 'https://www.state.gov/key-topics-bureau-of-international-security-and-nonproliferation/nonproliferation-sanctions/'
    source_name = 'Nonproliferation Sanctions (ISN) - State Department'
    expected_headers = frozenset({
        'Source List', 'Programs',
        'Name', 'Alternative Names', 'Country',
        'Federal Register Notice', 'Effective Date',
        'Remarks/Notes', 'Web Link'
    })

    logging.info('Checking last updated')
    last_modified = urllib.request.urlopen(isn_meta_url).read().decode('utf-8').strip()
    response = urllib.request.urlopen(url)
    latest_modified = response.info()['Last-Modified']
    if last_modified == latest_modified:
        logging.info('No new data. Skipping processing.')
        return 0

    logging.info('Requesting data file')
    lines = [line.decode('utf-8') for line in response.readlines()]
    csvfile = csv.DictReader(lines)
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
    for row in csvfile:
        key = row['Name'].lower().strip() + row['Federal Register Notice'].lower().strip()
        h = hashlib.sha224(key.encode()).hexdigest()
        if h in seen.keys():
            seen[h]['Programs'] = f"{seen[h]['Programs']} + {row['Programs']}"
        else:
            seen[h] = row

    for key, value in seen.items():
        start_date = convert_date.parse_american_date(value['Effective Date'])
        doc = {
            '_id': key,
            'source': source_name,
            'programs': value['Programs'].split(' + '),
            'name': value['Name'],
            'country': country_code.get_country_code(value['Country']),
            'federal_register_notice': value['Federal Register Notice'],
            'start_date': start_date if start_date else None,
            'remarks': value['Remarks/Notes'] or None,
            'source_list_url': source_information_url,
            'alt_names': value['Alternative Names'],
            'source_information_url': source_information_url,
        }
        country_keep = doc['country']
        del doc['country']
        programs_keep = doc['programs']
        doc['programs'] = '; '.join(doc['programs'])
        csv_writer.writerow(doc)
        tsv_writer.writerow(doc)
        doc['id'] = doc['_id']
        del doc['_id']
        doc['country'] = country_keep
        doc['programs'] = programs_keep
        doc['alt_names'] = doc['alt_names'].replace(", and", ",")
        doc['alt_names'] = doc['alt_names'].split(', ') if doc['alt_names'] else None
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
