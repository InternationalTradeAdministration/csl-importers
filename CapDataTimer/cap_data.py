import csv
import json
import logging
import os
import urllib.request

from azure.storage.blob import BlobServiceClient, ContentSettings
from io import StringIO

from shared import csl_meta, nested_fields, output

from sanctions_list_parser import SanctionsListParser

connection_string = os.environ["CONNECTION_STRING"]
csl_container = os.environ["CSL_CONTAINER"]
ns = {'xmlns': 'http://tempuri.org/sdnList.xsd'}

source_abbr = 'cap'
source_name = 'Capta List (CAP) - Treasury Department'
source_list_url = 'https://www.treasury.gov/ofac/downloads/sanctions/1.0/cons_advanced.xml'
source_information_url = 'https://home.treasury.gov/policy-issues/financial-sanctions/consolidated-sanctions-list-non-sdn-lists/list-of-foreign-financial-institutions-subject-to-correspondent-account-or-payable-through-account-sanctions-capta-list'

address_path = 'xmlns:addressList/xmlns:address'
alt_names_path = 'xmlns:akaList/xmlns:aka'
citizenship_path = 'xmlns:citizenshipList/xmlns:citizenship/xmlns:country'
dob_path = 'xmlns:dateOfBirthList/xmlns:dateOfBirthItem/xmlns:dateOfBirth'
id_path = 'xmlns:idList/xmlns:id'

null_fields = [
    'call_sign', 'end_date', 'federal_register_notice',
    'gross_registered_tonnage', 'gross_tonnage',
    'license_policy', 'license_requirement',
    'nationalities', 'places_of_birth', 'standard_order',
    'start_date', 'title', 'vessel_flag',
    'vessel_owner', 'vessel_type'
]


def main():
    logging.info('Checking last updated')
    last_modified = csl_meta.get_meta_url_last_modified(source_abbr)

    response = urllib.request.urlopen(source_list_url)
    latest_modified = response.info()['Last-Modified']
    if last_modified == latest_modified:
        logging.info('No new data. Skipping processing.')
        return 0

    logging.info('Requesting data file')

    sanction_list_parser = SanctionsListParser(response)
    capta_list = sanction_list_parser.get_sanctions_list_by_name('capta')
    logging.info(f'capta_list {capta_list}')
    sanctions_entries = sanction_list_parser.get_sanctions_entries_by_list_id(capta_list['id'])

    logging.info('Processing data')
    csv_output = StringIO()
    tsv_output = StringIO()
    json_output = StringIO()
    csv_writer = csv.DictWriter(csv_output, fieldnames=output.output_fields, dialect='unix')
    tsv_writer = csv.DictWriter(tsv_output, fieldnames=output.output_fields, dialect='unix', delimiter='\t')
    csv_writer.writeheader()
    tsv_writer.writeheader()
    doc_list = []

    for sanctions_entry in sanctions_entries:
        sanctions_entry['id'] = f'{sanctions_entry["id"]}'
        sanctions_entry['entity_number'] = sanctions_entry['id']
        sanctions_entry['source'] = source_name
        sanctions_entry['source_information_url'] = source_information_url
        sanctions_entry['source_list_url'] = source_list_url

        for f in null_fields:
            sanctions_entry[f] = None

        doc_copy = sanctions_entry.copy()
        doc_list.append(doc_copy)

        sanctions_entry['addresses'] = nested_fields.make_flat_address(sanctions_entry['addresses'])
        sanctions_entry['alt_names'] = '; '.join(sanctions_entry['alt_names'])
        sanctions_entry['programs'] = '; '.join(sanctions_entry['programs'])
        sanctions_entry['_id'] = sanctions_entry['id']
        del sanctions_entry['id']
        id_list = []
        for d in sanctions_entry['ids']:
            id_list.append(", ".join([v for v in d.values() if v]))
        sanctions_entry['ids'] = "; ".join(id_list)
        tsv_writer.writerow(sanctions_entry)
        csv_writer.writerow(sanctions_entry)

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
