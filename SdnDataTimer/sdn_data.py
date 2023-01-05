import csv
import json
import logging
import os
import xml.etree.ElementTree as ET
import urllib.request

from azure.storage.blob import BlobServiceClient, ContentSettings
from io import StringIO

from shared import citizenship, csl_meta, name_extractor, nested_fields, output

connection_string = os.environ["CONNECTION_STRING"]
csl_container = os.environ["CSL_CONTAINER"]
ns = {'xmlns': 'http://tempuri.org/sdnList.xsd'}

source_abbr = 'sdn'
source_name = 'Specially Designated Nationals (SDN) - Treasury Department'
source_list_url = 'https://www.treasury.gov/resource-center/sanctions/SDN-List/Pages/default.aspx'
source_information_url = 'https://home.treasury.gov/policy-issues/financial-sanctions/specially-designated-nationals-and-blocked-persons-list-sdn-human-readable-lists'

address_path = 'xmlns:addressList/xmlns:address'
alt_names_path = 'xmlns:akaList/xmlns:aka'
citizenship_path = 'xmlns:citizenshipList/xmlns:citizenship/xmlns:country'
dob_path = 'xmlns:dateOfBirthList/xmlns:dateOfBirthItem'
pob_path = 'xmlns:placeOfBirthList/xmlns:placeOfBirthItem'
id_path = 'xmlns:idList/xmlns:id'
nationality_path = 'xmlns:nationalityList/xmlns:nationality'

null_fields = [
    'end_date', 'federal_register_notice',
    'license_policy', 'license_requirement'
]


def main():
    logging.info('Checking last updated')
    last_modified = csl_meta.get_meta_url_last_modified(source_abbr)
    url = 'https://www.treasury.gov/ofac/downloads/sdn.xml'
    response = urllib.request.urlopen(url)
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

        doc['entity_number'] = entry.find('xmlns:uid', ns).text.strip()
        doc['id'] = entry.find('xmlns:uid', ns).text.strip()
        doc['name'] = name_extractor.get_name(entry, "lastfirst")
        doc['programs'] = programs
        remarks = entry.find('xmlns:remarks', ns)
        doc['remarks'] = remarks.text if remarks is not None else None
        doc['source'] = source_name
        doc['source_information_url'] = source_information_url
        doc['source_list_url'] = source_list_url
        title = entry.find('xmlns:title', ns)
        doc['title'] = title.text.strip() if title is not None else None
        doc['type'] = entry.find('xmlns:sdnType', ns).text.strip()

        addresses = entry.findall(address_path, ns)
        doc['addresses'] = nested_fields.get_multiline_addresses(addresses)
        alt_names = entry.findall(alt_names_path, ns)
        doc['alt_names'] = name_extractor.get_alt_names(alt_names, "lastfirst")
        citizenships = entry.findall(citizenship_path, ns)
        ctznships = citizenship.get_citizenship(citizenships)
        doc['citizenships'] = [] if ctznships is None else ctznships
        dates_of_birth = entry.findall(dob_path, ns)
        doc['dates_of_birth'] = nested_fields.get_dates_of_birth(dates_of_birth)
        places_of_birth = entry.findall(pob_path, ns)
        doc['places_of_birth'] = nested_fields.get_places_of_birth(places_of_birth)
        nationalities = entry.findall(nationality_path, ns)
        doc['nationalities'] = nested_fields.get_nationalities(nationalities)
        ids = entry.findall(id_path, ns)
        doc['ids'] = nested_fields.get_ids(ids)

        call_sign = entry.find('xmlns:vesselInfo/xmlns:callSign', ns)
        doc['call_sign'] = call_sign.text if call_sign is not None else None
        grt = entry.find('xmlns:vesselInfo/xmlns:grossRegisteredTonnage', ns)
        doc['gross_registered_tonnage'] = grt.text if grt is not None else None
        gt = entry.find('xmlns:vesselInfo/xmlns:tonnage', ns)
        doc['gross_tonnage'] = gt.text if gt is not None else None
        vf = entry.find('xmlns:vesselInfo/xmlns:vesselFlag', ns)
        doc['vessel_flag'] = vf.text if vf is not None else None
        vo = entry.find('xmlns:vesselInfo/xmlns:vesselOwner', ns)
        doc['vessel_owner'] = vo.text if vo is not None else None
        vt = entry.find('xmlns:vesselInfo/xmlns:vesselType', ns)
        doc['vessel_type'] = vt.text if vt is not None else None

        for f in null_fields:
            doc[f] = None

        doc = dict(sorted(doc.items()))
        doc_copy = doc.copy()
        doc_list.append(doc_copy)

        doc['addresses'] = nested_fields.make_flat_address(doc['addresses'])
        for i in ['alt_names', 'citizenships',
                  'programs', 'dates_of_birth',
                  'places_of_birth', 'nationalities']:
            doc[i] = '; '.join(doc[i])
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
    blob_client = blob_service_client.get_blob_client(container=csl_container, blob=f"sdn_meta.txt")
    blob_client.upload_blob(latest_modified, overwrite=True, content_settings=content_setting)
    json_output.close()
