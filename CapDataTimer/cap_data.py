import csv
import json
import logging
import os
import xml.etree.ElementTree as ET
import urllib.request

from azure.storage.blob import BlobServiceClient, ContentSettings
from io import StringIO

from shared import citizenship, convert_date, \
    name_extractor, nested_fields, output

connection_string = os.environ["CONNECTION_STRING"]
csl_container = os.environ["CSL_CONTAINER"]
treasury_meta_url = os.environ['TREASURY_META_URL']
ns = {'xmlns': 'http://tempuri.org/sdnList.xsd'}

source_abbr = 'cap'
source_name = 'Capta List (CAP) - Treasury Department'
source_list_url = 'https://www.treasury.gov/ofac/downloads/consolidated/consolidated.xml'
source_information_url = 'https://home.treasury.gov/policy-issues/office-of-foreign-assets-control-sanctions-programs-and-information'

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
    last_modified = urllib.request.urlopen(treasury_meta_url).read().decode('utf-8').strip()
    response = urllib.request.urlopen(source_list_url)
    latest_modified = response.info()['Last-Modified']
    if last_modified == latest_modified:
        logging.info('No new data. Skipping processing.')
        return 0

    logging.info('Requesting data file')
    tree = ET.parse(response)
    root = tree.getroot()

    logging.info('Processing data')
    csv_output = StringIO()
    tsv_output = StringIO()
    json_output = StringIO()
    csv_writer = csv.DictWriter(csv_output, fieldnames=output.output_fields, dialect='unix')
    tsv_writer = csv.DictWriter(tsv_output, fieldnames=output.output_fields, dialect='unix', delimiter='\t')
    csv_writer.writeheader()
    tsv_writer.writeheader()
    doc_list = []
    for entry in root.findall('xmlns:sdnEntry', ns):
        doc = {}
        programs = entry.find('xmlns:programList', ns)
        programs = [p.text for p in programs]
        if '561-Related' in programs or 'RUSSIA-EO14024' in programs:
            ids = entry.findall(id_path, ns)
            doc['ids'] = nested_fields.get_ids(ids)
            if 'RUSSIA-EO14024' in programs:
                vals = [val for d in doc['ids'] for val in d.values() if val]
                if 'Effective Date (EO 14024 Directive 2):' not in vals:
                    continue

            doc['entity_number'] = entry.find('xmlns:uid', ns).text.strip()
            doc['id'] = entry.find('xmlns:uid', ns).text.strip()
            doc['name'] = name_extractor.get_name(entry)
            doc['programs'] = programs
            remarks = entry.find('xmlns:remarks', ns)
            doc['remarks'] = remarks.text if remarks is not None else None
            doc['source'] = source_name
            doc['source_information_url'] = source_information_url
            doc['source_list_url'] = source_list_url
            doc['type'] = entry.find('xmlns:sdnType', ns).text.strip()

            addresses = entry.findall(address_path, ns)
            doc['addresses'] = nested_fields.get_multiline_addresses(addresses)
            alt_names = entry.findall(alt_names_path, ns)
            doc['alt_names'] = name_extractor.get_alt_names(alt_names)
            citizenships = entry.findall(citizenship_path, ns)
            doc['citizenships'] = citizenship.get_citizenship(citizenships)
            dob = entry.find(dob_path, ns)
            doc['dates_of_birth'] = convert_date.parse_date(dob.text) if dob is not None else None

            for f in null_fields:
                doc[f] = None

            doc = dict(sorted(doc.items()))
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
    blob_client = blob_service_client.get_blob_client(container=csl_container, blob=f"treasury_meta.txt")
    blob_client.upload_blob(latest_modified, overwrite=True, content_settings=content_setting)
    json_output.close()
