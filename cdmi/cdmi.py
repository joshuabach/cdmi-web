import json
import requests
import logging

from requests.compat import urljoin, urlsplit
from requests.exceptions import ConnectionError
from json import JSONDecodeError

from django.contrib import messages
from django.conf import settings

from .models import Site

logger = logging.getLogger(__name__)


def _auth_method(url):
    # TODO It's a bit hacky to reverse engineere the Site from the url
    urlcomponents = urlsplit(url)
    site_uri = urlcomponents.scheme + '://' + urlcomponents.netloc
    method = Site.objects.get(site_uri=site_uri).auth
    logger.debug('Using {} authentication to access {}'.format(method, url))
    return method


def _request_auth_kwargs(url, request):
    if _auth_method(url) == 'basic':
        return {'auth': ('restadmin', 'restadmin'),
                'headers': {}}
    else:
        return {'headers': {'Authorization': 'Bearer {}'.format(
            request.session['access_token'])}}


def _update_qos_cdmi(url, request, body):
    request_kwargs = _request_auth_kwargs(url, request)
    request_kwargs['headers']['Content-Type'] = 'application/cdmi-object'
    request_kwargs['json'] = body

    json_response = dict()
    try:
        r = requests.put(url, **request_kwargs)
        json_response = r.json()
        logger.debug(json_response)
    except (ConnectionError):
        logger.warning('Could not connect to CDMI host {}'.format(url))
    except (JSONDecodeError):
        logger.warning('Error decoding JSON from CDMI host {}'.format(url))

    return json_response

def _query_cdmi(url, request):
    request_kwargs = _request_auth_kwargs(url, request)

    json_response = dict()
    try:
        r = requests.get(url, **request_kwargs)
        json_response = r.json()
        logger.debug(json_response)
    except (ConnectionError):
        logger.warning('Could not connect to CDMI host {}'.format(url))
    except (JSONDecodeError):
        logger.warning('Error decoding JSON from CDMI host {}'.format(url))

    return json_response

def put_capabilities_class(path, request, capabilities):
    cdmi_uri = settings.CDMI_URI
    url = urljoin(cdmi_uri, path)

    body = {'capabilitiesURI': capabilities}
    response = _update_qos_cdmi(url, request, body)

    return response

def get_status(path, request):
    cdmi_uri = settings.CDMI_URI
    url = urljoin(cdmi_uri, path)

    status = _query_cdmi(url, request)

    return status

def get_capabilities_class(url, request, classes=None):
    capabilities = _query_cdmi(url, request)

    capabilities_class = dict()
    try:
        name = capabilities['objectName']
        copies = capabilities['metadata']['cdmi_data_redundancy']
        latency = capabilities['metadata']['cdmi_latency']
        location = capabilities['metadata']['cdmi_geographic_placement']
        transitions = capabilities['metadata']['cdmi_capabilities_allowed']
        transitions = [ x.rsplit('/', 1)[-1] for x in transitions ]

        datapath = ''
        if urlsplit(url).netloc == 'localhost:8888':
            datapath = settings.DATA_ENDPOINT

        qos = []
        if int(latency) < 200:
            qos.append('processing')
        if int(copies) > 2:
            qos.append('archiving')

        capabilities_class = dict(name=name, latency=latency, copies=copies, location=location,
                qos=qos, transitions=transitions, url=url, datapath=datapath)

    except (KeyError):
        logger.warning('Wrong or missing CDMI capabilities at {}'.format(url))

    return capabilities_class

def get_all_capabilities(url, request):
    capabilities_url = urljoin(url, 'cdmi_capabilities/dataobject')
    capabilities = _query_cdmi(capabilities_url, request)

    all_capabilities = []
    try:
        for child in capabilities['children']:
            child_url = urljoin(url, 'cdmi_capabilities/dataobject/{}'.format(child))

            capabilities_class = get_capabilities_class(child_url, request)

            all_capabilities.append(capabilities_class)
    except (KeyError):
        logger.warning('Key error for {}'.format(url))

    return all_capabilities