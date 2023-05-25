import csv
import json
import hashlib
import logging
import os

from azure.storage.blob import BlobServiceClient, ContentSettings
from io import StringIO

from shared import country_code, csl_meta, output, request

connection_string = os.environ["CONNECTION_STRING"]
csl_container = os.environ["CSL_CONTAINER"]
source_abbr = 'uvl'


def main():
    url = 'https://www.bis.doc.gov/index.php/component/docman/?task=doc_download&gid=1053'
    source_list_url = 'https://www.bis.doc.gov/index.php/policy-guidance/lists-of-parties-of-concern/unverified-list'
    source_information_url = 'https://www.bis.doc.gov/index.php/policy-guidance/lists-of-parties-of-concern/unverified-list'
    source_name = 'Unverified List (UVL) - Bureau of Industry and Security'
    expected_headers = frozenset({'COUNTRY', 'NAME', 'ADDRESS'})

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
    source_csv_fields = csvfile.fieldnames
    logging.info('Checking header')
    if not expected_headers.issubset(set(source_csv_fields)):
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
        key = row['NAME'].lower().strip()
        h = hashlib.sha224(key.encode()).hexdigest()
        if h in seen.keys():
            cc = country_code.get_country_code(row['COUNTRY'])
            address = f"{row['ADDRESS']}, {cc}"
            seen[h]['flat_address'] = f"{seen[h]['flat_address']}; {address}"
            additional_address = {
                'address': row['ADDRESS'],
                'city': None,
                'state': None,
                'postal_code': None,
                'country': cc
            }
            address_dict[h].append(additional_address)
        else:
            cc = country_code.get_country_code(row['COUNTRY'])
            row['flat_address'] = f"{row['ADDRESS']}, {cc}"
            seen[h] = row
            address_dict[h] = [{
                'address': row['ADDRESS'],
                'city': None,
                'state': None,
                'postal_code': None,
                'country': cc
            }]

    for key, value in seen.items():
        doc = {
            '_id': key,
            'source': source_name,
            'name': value['NAME'],
            'addresses': value['flat_address'],
            'source_list_url': source_list_url,
            'source_information_url': source_information_url,
        }
        csv_writer.writerow(doc)
        tsv_writer.writerow(doc)
        doc['id'] = doc['_id']
        del doc['_id']
        doc['addresses'] = [addr for addr in address_dict[key]]
        doc['alt_names'] = []
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
