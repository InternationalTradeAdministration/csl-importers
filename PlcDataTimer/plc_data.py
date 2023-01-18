import csv
import json
import logging
import os
import urllib.request

from azure.storage.blob import BlobServiceClient, ContentSettings
from io import StringIO

from shared import csl_meta, output, treasury_consolidated_handler

CONNECTION_STRING = os.environ["CONNECTION_STRING"]
CSL_CONTAINER = os.environ["CSL_CONTAINER"]

SOURCE_ABBR = 'plc'
SOURCE = 'Palestinian Legislative Council List (PLC) - Treasury Department'
SOURCE_INFORMATION_URL = 'https://home.treasury.gov/policy-issues/financial-sanctions/consolidated-sanctions-list/non-sdn-palestinian-legislative-council-ns-plc-list'
SOURCE_LIST_URL = 'https://www.treasury.gov/ofac/downloads/consolidated/consolidated.xml'

SOURCE_DETAILS = {
    'source': SOURCE,
    'source_information_url': SOURCE_INFORMATION_URL,
    'source_list_url': SOURCE_LIST_URL
}


def main():
    logging.info('Checking last updated')
    last_modified = csl_meta.get_meta_url_last_modified(SOURCE_ABBR)

    response = urllib.request.urlopen(SOURCE_LIST_URL)
    latest_modified = response.info()['Last-Modified']
    if last_modified == latest_modified:
        logging.info('No new data. Skipping processing.')
        return 0

    logging.info('parsing response')
    entries = treasury_consolidated_handler.entries(response)

    logging.info('Processing data')
    csv_output = StringIO()
    tsv_output = StringIO()
    json_output = StringIO()
    csv_writer = csv.DictWriter(csv_output, fieldnames=output.output_fields, dialect='unix')
    tsv_writer = csv.DictWriter(tsv_output, fieldnames=output.output_fields, dialect='unix', delimiter='\t')
    csv_writer.writeheader()
    tsv_writer.writeheader()
    doc_list = []
    for entry in entries:
        doc = treasury_consolidated_handler.extract(entry)
        if 'NS-PLC' in doc['programs']:
            doc.update(SOURCE_DETAILS)
            doc = dict(sorted(doc.items()))

            doc_copy = doc.copy()
            doc_list.append(doc_copy)

            doc = treasury_consolidated_handler.flatten_list(doc)
            tsv_writer.writerow(doc)
            csv_writer.writerow(doc)

    json.dump(doc_list, json_output)

    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    logging.info('Write csv file')
    content_setting = ContentSettings(content_type='text/csv')
    blob_client = blob_service_client.get_blob_client(container=CSL_CONTAINER, blob=f"{SOURCE_ABBR}.csv")
    blob_client.upload_blob(csv_output.getvalue(), overwrite=True, content_settings=content_setting)
    csv_output.close()
    logging.info('Write tsv file')
    content_setting = ContentSettings(content_type='text/tsv')
    blob_client = blob_service_client.get_blob_client(container=CSL_CONTAINER, blob=f"{SOURCE_ABBR}.tsv")
    blob_client.upload_blob(tsv_output.getvalue(), overwrite=True, content_settings=content_setting)
    tsv_output.close()
    logging.info('Write json file')
    content_setting = ContentSettings(content_type='application/json')
    blob_client = blob_service_client.get_blob_client(container=CSL_CONTAINER, blob=f"{SOURCE_ABBR}.json")
    blob_client.upload_blob(json_output.getvalue(), overwrite=True, content_settings=content_setting)
    json_output.close()
    logging.info('Write last modified file')
    content_setting = ContentSettings(content_type='text/plain')
    blob_client = blob_service_client.get_blob_client(container=CSL_CONTAINER, blob=f"{SOURCE_ABBR}_meta.txt")
    blob_client.upload_blob(latest_modified, overwrite=True, content_settings=content_setting)
    json_output.close()
