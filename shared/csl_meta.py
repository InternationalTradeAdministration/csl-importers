import logging
import os
import urllib.request
from urllib.error import HTTPError


def get_meta_url(source_abbr):
    return f"{os.environ['META_HOST_URL']}/{os.environ['CSL_CONTAINER']}/{source_abbr}_meta.txt"


def get_meta_url_last_modified(source_abbr, encoding='utf-8'):
    last_modified = 'N/A'
    meta_url = get_meta_url(source_abbr)
    try:
        last_modified = urllib.request.urlopen(meta_url).read().decode(encoding).strip()
    except HTTPError:
        logging.exception('Unable to read data from %s', meta_url)

    return last_modified
