import csv
import json
import os
import logging

import urllib.request

from azure.storage.blob import BlobServiceClient, ContentSettings
from io import StringIO

from . import csl_meta, nested_fields, output, treasury_metadata

from ..sanctions_list_parser import TreasuryProcessor


connection_string = os.environ["CONNECTION_STRING"]
csl_container = os.environ["CSL_CONTAINER"]

null_fields = [
    'call_sign', 'end_date', 'federal_register_notice',
    'gross_registered_tonnage', 'gross_tonnage',
    'license_policy', 'license_requirement',
    'nationalities', 'places_of_birth', 'standard_order',
    'start_date', 'title', 'vessel_flag',
    'vessel_owner', 'vessel_type'
]


def run_import(source_abbr):
    logging.info('Checking last updated')
    last_modified = csl_meta.get_meta_url_last_modified(source_abbr)

    source_metadata = treasury_metadata.get_treasury_metadata(source_abbr)

    logging.info('Requesting data file')
    response = urllib.request.urlopen(source_metadata['list_url'])
    latest_modified = response.info()['Last-Modified']
    if last_modified == latest_modified:
        logging.info('No new data. Skipping processing.')
        return 0

    list_id = source_metadata['list_id']
    logging.info(f'Processing {source_abbr} data with list_id {list_id}')
    processor = TreasuryProcessor(response)
    sanctions_entries = processor.get_sanctions_entries(list_id)

    csv_output = StringIO()
    tsv_output = StringIO()
    json_output = StringIO()
    csv_writer = csv.DictWriter(csv_output, fieldnames=output.output_fields, dialect='unix')
    tsv_writer = csv.DictWriter(tsv_output, fieldnames=output.output_fields, dialect='unix', delimiter='\t')
    csv_writer.writeheader()
    tsv_writer.writeheader()
    doc_list = []

    source_info = {
        'source': source_metadata['source'],
        'source_information_url': source_metadata['list_information_url'],
        'source_list_url': source_metadata['list_url']
    }

    for sanctions_entry in sanctions_entries:
        sanctions_entry.update(source_info)

        doc = dict(sorted(sanctions_entry.items()))
        doc_copy = doc.copy()
        doc_list.append(doc_copy)

        doc['addresses'] = nested_fields.make_flat_address(doc['addresses'])
        doc['alt_names'] = '; '.join(doc['alt_names'])
        doc['programs'] = '; '.join(doc['programs'])
        doc['_id'] = doc['id']
        del doc['id']
        id_list = []
        for d in doc['ids']:
            id_list.append(", ".join([v for v in d.values() if v]))
        doc['ids'] = "; ".join(id_list)
        tsv_writer.writerow(doc)
        csv_writer.writerow(doc)

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
