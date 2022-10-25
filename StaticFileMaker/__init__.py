import datetime
import json
import logging
import os

import urllib.request

import azure.functions as func
from azure.storage.blob import BlobServiceClient, ContentSettings
from io import StringIO

connection_string = os.environ['CONNECTION_STRING']
csl_container = os.environ['CSL_CONTAINER']
csl_static_container = os.environ['CSL_STATIC_CONTAINER']
dpl_meta_url = os.environ['DPL_META_URL']
dtc_meta_url = os.environ['DTC_META_URL']
el_meta_url = os.environ['EL_META_URL']
isn_meta_url = os.environ['ISN_META_URL']
meu_meta_url = os.environ['MEU_META_URL']
sdn_meta_url = os.environ['SDN_META_URL']
treasury_meta_url = os.environ['TREASURY_META_URL']
uvl_meta_url = os.environ['UVL_META_URL']

json_out = 'consolidated.json'
data_file_list = [
    'cmic.json', 'cap.json', 'dpl.json',
    'dtc.json', 'el.json', 'fse.json',
    'isn.json', 'mbs.json', 'meu.json',
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

    dtc_res = urllib.request.urlopen(dtc_meta_url).read().decode('utf-8').strip()
    dtc_date = datetime.datetime.strptime(dtc_res, '%m.%d.%y')
    dtc_updated = dtc_date.strftime('%Y-%m-%dT%H:%M:%S+00:00')

    dpl_updated = get_date(dpl_meta_url)
    el_updated = get_date(el_meta_url)
    isn_updated = get_date(isn_meta_url)
    meu_updated = get_date(meu_meta_url)
    sdn_updated = get_date(sdn_meta_url)
    treasury_updated = get_date(treasury_meta_url)
    uvl_updated = get_date(uvl_meta_url)

    doc_dict = {
        "results": doc_list,
        "search_performed_at": utc_timestamp,
        "sources_used": [
            {
                "last_imported": utc_timestamp,
                "source_last_updated": treasury_updated,
                "source": "Capta List (CAP) - Treasury Department",
                "import_rate": "Hourly"
            },
            {
                "last_imported": utc_timestamp,
                "source_last_updated": treasury_updated,
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
                "source_last_updated": treasury_updated,
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
                "source_last_updated": treasury_updated,
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
                "source_last_updated": sdn_updated,
                "source": "Specially Designated Nationals (SDN) - Treasury Department",
                "import_rate": "Hourly"
            },
            {
                "last_imported": utc_timestamp,
                "source_last_updated": treasury_updated,
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
