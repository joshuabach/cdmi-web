import json
import requests
import logging

from requests.compat import urljoin
from requests.exceptions import ConnectionError
from json import JSONDecodeError

from django.contrib import messages
from django.conf import settings

logger = logging.getLogger(__name__)

def get_status(path):
    cdmi_uri = settings.CDMI_URI
    #access_token = request.session['access_token']
    #headers = {'Authorization': 'Bearer {}'.format(access_token)}
    url = urljoin(cdmi_uri, path)
    status = dict()
    try:
        r = requests.get(url, auth=('restadmin', 'restadmin')) # headers=headers)
        status = r.json()
        logger.debug(status)
    except (ConnectionError):
        logger.warning('Could not connect to CDMI host {}'.format(cdmi_uri))
    except (JSONDecodeError):
        logger.warning('Error decoding JSON from CDMI host {}'.format(cdmi_uri))

    return status
