import csv
import logging
import json
import os
import re
import uuid

import urllib.request

from azure.storage.blob import BlobServiceClient, ContentSettings
from io import StringIO
from shared import csl_meta, output

connection_string = os.environ["CONNECTION_STRING"]
csl_container = os.environ["CSL_CONTAINER"]
source_abbr = 'dtc'


def main():
    stat_debarred_url = 'https://www.pmddtc.state.gov/sys_attachment.do?sys_id=5d03bca21b2255102dc36311f54bcb91'
    admin_debarred_url = 'https://www.pmddtc.state.gov/sys_attachment.do?sys_id=d78bbc2f1b8f29d0c6c3866ae54bcbd7'
    source_information_url = 'https://www.pmddtc.state.gov/ddtc_public?id=ddtc_kb_article_page&sys_id=c22d1833dbb8d300d0a370131f9619f0'
    source_name = 'ITAR Debarred (DTC) - State Department'

    stat_expected_headers = frozenset({
        'Party Name', 'Date Of Birth', 'Federal Register Notice',
        'Notice Date', 'Corrected Notice', 'Corrected Notice Date'
    })
    admin_expected_headers = frozenset({
        'Name', 'Date', 'Charging Letter',
        'Debarment Order', 'Federal Register Notice'
    })

    logging.info(f"Checking stat last updated {stat_debarred_url}")
    stat_last_modified = csl_meta.get_meta_url_last_modified(f"{source_abbr}_stat", 'utf-8-sig')
    stat_response = urllib.request.urlopen(stat_debarred_url)
    stat_latest_modified = extract_latest_modified(stat_response)

    logging.info(f"Checking admin last updated {admin_debarred_url}")
    admin_last_modified = csl_meta.get_meta_url_last_modified(f"{source_abbr}_admin", 'utf-8-sig')
    admin_response = urllib.request.urlopen(admin_debarred_url)
    admin_latest_modified = extract_latest_modified(admin_response)

    if stat_last_modified == stat_latest_modified and admin_last_modified == admin_latest_modified:
        logging.info('No new data. Skipping processing.')
        return 0

    logging.info('reading stat data')
    stat_lines = [line.decode('utf-8-sig') for line in stat_response.readlines()]
    stat_csvfile = csv.DictReader(stat_lines)
    source_csv_fields = stat_csvfile.fieldnames

    logging.info('Checking header')
    if not set(source_csv_fields) == (stat_expected_headers):
        raise ValueError("Actual headers differ from expected. Stat.")

    logging.info('reading admin data')
    admin_lines = [line.decode('utf-8') for line in admin_response.readlines()]
    admin_csvfile = csv.DictReader(admin_lines)
    admin_csv_fields = admin_csvfile.fieldnames

    logging.info('Checking header')
    if not set(admin_csv_fields) == (admin_expected_headers):
        raise ValueError("Actual headers differ from expected. Admin.")

    logging.info('Processing data')
    csv_output = StringIO()
    tsv_output = StringIO()
    json_output = StringIO()
    csv_writer = csv.DictWriter(csv_output, fieldnames=output.output_fields, dialect='unix')
    tsv_writer = csv.DictWriter(tsv_output, fieldnames=output.output_fields, dialect='unix', delimiter='\t')
    csv_writer.writeheader()
    tsv_writer.writeheader()

    doc_list = []
    for row in stat_csvfile:
        id = uuid.uuid4().hex
        name, alt_names = process_names(row['Party Name'])
        federal_register_notice = row['Corrected Notice'] if row['Corrected Notice'] else row['Federal Register Notice']
        doc = {
                '_id': id,
                'alt_names': alt_names,
                'federal_register_notice': federal_register_notice,
                'name': name,
                'source': source_name,
                'source_list_url': source_information_url,
                'source_information_url': source_information_url,
        }
        csv_writer.writerow(doc)
        tsv_writer.writerow(doc)
        doc['id'] = doc['_id']
        del doc['_id']
        doc['alt_names'] = doc['alt_names'].split('; ') if doc['alt_names'] else []
        doc_list.append(doc)

    for row in admin_csvfile:
        id = uuid.uuid4().hex
        doc = {
                '_id': id,
                'name': row['Name'],
                'alt_names': [],
                'federal_register_notice': row['Federal Register Notice'],
                'source': source_name,
                'source_list_url': source_information_url,
                'source_information_url': source_information_url,
        }
        csv_writer.writerow(doc)
        tsv_writer.writerow(doc)
        doc['id'] = doc['_id']
        del doc['_id']
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
    blob_client = blob_service_client.get_blob_client(container=csl_container, blob=f"{source_abbr}_stat_meta.txt")
    blob_client.upload_blob(stat_latest_modified, overwrite=True, content_settings=content_setting)
    blob_client = blob_service_client.get_blob_client(container=csl_container, blob=f"{source_abbr}_admin_meta.txt")
    blob_client.upload_blob(admin_latest_modified, overwrite=True, content_settings=content_setting)


def extract_latest_modified(response):
    latest_filename = response.info()['Content-Disposition']
    return re.search(r"\_(\d{1,2}\.\d{1,2}\.\d{2})", latest_filename).group(1)

def process_names(names):
    if '(a.k.a. ' in names or '(aka ' in names:
        try:
            res = re.search(r'\(.*\)', names)
            alt_names = extract_alt_names(res.group())
            name = re.sub(r' \(.*\)', '', names)
            name = extract_name(name)
        except AttributeError:
            alt_names = ''
            name = extract_name(names)
    else:
        alt_names = ''
        name = extract_name(names)
    return name, alt_names


def extract_alt_names(alt_names):
    alts = re.sub('[()]', '', alt_names)
    return alts.replace('a.k.a. ', '').replace('aka ', '')


def extract_name(name):
    if 'Inc.' in name:
        return name
    else:
        return ' '.join(reversed(name.split(', ')))
