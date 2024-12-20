import datetime
import json
import logging
import os

import urllib.request

import azure.functions as func
from azure.storage.blob import BlobServiceClient, ContentSettings
from io import StringIO

from ..shared import csl_meta

connection_string = os.environ['CONNECTION_STRING']
csl_container = os.environ['CSL_CONTAINER']
csl_static_container = os.environ['CSL_STATIC_CONTAINER']
cap_meta_url = csl_meta.get_meta_url('cap')
cmic_meta_url = csl_meta.get_meta_url('cmic')
dpl_meta_url = csl_meta.get_meta_url('dpl')
dtc_meta_url = csl_meta.get_meta_url('dtc')
el_meta_url = csl_meta.get_meta_url('el')
fse_meta_url = csl_meta.get_meta_url('fse')
isn_meta_url = csl_meta.get_meta_url('isn')
mbs_meta_url = csl_meta.get_meta_url('mbs')
meu_meta_url = csl_meta.get_meta_url('meu')
plc_meta_url = csl_meta.get_meta_url('plc')
sdn_meta_url = csl_meta.get_meta_url('sdn')
ssi_meta_url = csl_meta.get_meta_url('ssi')
uvl_meta_url = csl_meta.get_meta_url('uvl')

json_out = 'consolidated.json'
data_file_list = [
    'cmic.json', 'cap.json', 'dpl.json',
    'dtc.json', 'el.json', 'fse.json',
    'isn.json', 'mbs.json', 'meu.json',
    'plc.json',
    'sdn.json', 'ssi.json', 'uvl.json'
]


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(csl_container)
    blobs_list = container_client.list_blobs()
    json_output = StringIO()
    doc_list = []
    entity_count = 0
    for blob in blobs_list:
        if blob.name in data_file_list:
            blob_client = container_client.get_blob_client(blob.name)
            streamdownloader = blob_client.download_blob()
            file = json.loads(streamdownloader.readall())
            for element in file:
                entity_count += 1
                doc_list.append(element)

    dtc_admin_last_modified = csl_meta.get_meta_url_last_modified('dtc_admin', 'utf-8-sig')
    dtc_admin_date = datetime.datetime.strptime(dtc_admin_last_modified, '%m.%d.%y')
    dtc_stat_last_modified = csl_meta.get_meta_url_last_modified('dtc_stat', 'utf-8-sig')
    dtc_stat_date = datetime.datetime.strptime(dtc_stat_last_modified, '%Y%m%d')
    dtc_date = dtc_admin_date if dtc_admin_date >= dtc_stat_date else dtc_stat_date
    dtc_updated = dtc_date.strftime('%Y-%m-%dT%H:%M:%S+00:00')

    cap_updated = get_date(cap_meta_url)
    cmic_updated = get_date(cmic_meta_url)
    dpl_updated = get_date(dpl_meta_url)
    el_updated = get_date(el_meta_url)
    fse_updated = get_date(fse_meta_url)
    isn_updated = get_date(isn_meta_url)
    mbs_updated = get_date(mbs_meta_url)
    meu_updated = get_date(meu_meta_url)
    plc_updated = get_date(plc_meta_url)
    sdn_updated = get_date(sdn_meta_url)
    ssi_updated = get_date(ssi_meta_url)
    uvl_updated = get_date(uvl_meta_url)

    doc_dict = {
        "results": doc_list,
        "search_performed_at": utc_timestamp,
        "sources_used": [
            {
                "last_imported": utc_timestamp,
                "source_last_updated": cap_updated,
                "source": "Capta List (CAP) - Treasury Department",
                "import_rate": "Hourly"
            },
            {
                "last_imported": utc_timestamp,
                "source_last_updated": cmic_updated,
                "source": "Non-SDN Chinese Military-Industrial Complex Companies List (CMIC) - Treasury Department",
                "import_rate": "Hourly"
            },
            {
                "last_imported": utc_timestamp,
                "source_last_updated": dpl_updated,
                "source": "Denied Persons List (DPL) - Bureau of Industry and Security",
                "import_rate": "Hourly"
            },
            {
                "last_imported": utc_timestamp,
                "source_last_updated": dtc_updated,
                "source": "ITAR Debarred (DTC) - State Department",
                "import_rate": "Hourly"
            },
            {
                "last_imported": utc_timestamp,
                "source_last_updated": el_updated,
                "source": "Entity List (EL) - Bureau of Industry and Security",
                "import_rate": "Hourly"
            },
            {
                "last_imported": utc_timestamp,
                "source_last_updated": fse_updated,
                "source": "Foreign Sanctions Evaders (FSE) - Treasury Department",
                "import_rate": "Hourly"
            },
            {
                "last_imported": utc_timestamp,
                "source_last_updated": isn_updated,
                "source": "Nonproliferation Sanctions (ISN) - State Department",
                "import_rate": "Hourly"
            },
            {
                "last_imported": utc_timestamp,
                "source_last_updated": mbs_updated,
                "source": "Non-SDN Menu-Based Sanctions List (NS-MBS List) - Treasury Department",
                "import_rate": "Hourly"
            },
            {
                "last_imported": utc_timestamp,
                "source_last_updated": meu_updated,
                "source": "Military End User (MEU) List - Bureau of Industry and Security",
                "import_rate": "Hourly"
            },
            {
                "last_imported": utc_timestamp,
                "source_last_updated": plc_updated,
                "source": "Palestinian Legislative Council List (PLC) - Treasury Department",
                "import_rate": "Hourly"
            },
            {
                "last_imported": utc_timestamp,
                "source_last_updated": sdn_updated,
                "source": "Specially Designated Nationals (SDN) - Treasury Department",
                "import_rate": "Hourly"
            },
            {
                "last_imported": utc_timestamp,
                "source_last_updated": ssi_updated,
                "source": "Sectoral Sanctions Identifications List (SSI) - Treasury Department",
                "import_rate": "Hourly"
            },
            {
                "last_imported": utc_timestamp,
                "source_last_updated": uvl_updated,
                "source": "Unverified List (UVL) - Bureau of Industry and Security",
                "import_rate": "Hourly"
            }
        ],
        "offset": 0,
        "total": entity_count
    }
    json.dump(doc_dict, json_output)

    content_setting = ContentSettings(content_type='application/json')
    blob_client = blob_service_client.get_blob_client(container=csl_static_container, blob=json_out)
    blob_client.upload_blob(json_output.getvalue(), overwrite=True, content_settings=content_setting)
    json_output.close()

    logging.info('Python timer trigger function ran at %s', utc_timestamp)


def get_date(url):
    res = urllib.request.urlopen(url).read().decode('utf-8').strip()
    date = datetime.datetime.strptime(res, '%a, %d %b %Y %H:%M:%S %Z')
    return date.strftime('%Y-%m-%dT%H:%M:%S+00:00')
