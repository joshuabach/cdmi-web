import requests
import logging

from requests.compat import urljoin, urlsplit
from requests.exceptions import ConnectionError
from json import JSONDecodeError

from django.conf import settings
from django.shortcuts import reverse

from .models import Site


logger = logging.getLogger(__name__)


def _auth_method(url):
    # TODO It's a bit hacky to reverse engineere the Site from the url
    urlcomponents = urlsplit(url)
    site_uri = urlcomponents.scheme + '://' + urlcomponents.netloc
    method = Site.objects.get(site_uri=site_uri).auth
    logger.debug('Using {} authentication to access {}'.format(method, url))
    return method


def _request_auth_kwargs(url, access_token):
    if _auth_method(url) == 'basic':
        return {'auth': ('restadmin', 'restadmin'),
                'headers': {}}
    else:
        return {'headers': {'Authorization': 'Bearer {}'.format(
            access_token)}}


def _update_qos_cdmi(url, access_token, is_dir, body):
    request_kwargs = _request_auth_kwargs(url, access_token)
    request_kwargs['headers']['Content-Type'] = (
        'application/cdmi-container' if is_dir else 'application/cdmi-object')
    request_kwargs['json'] = body

    json_response = dict()
    try:
        r = requests.put(url, **request_kwargs)
        json_response = r.json()
        logger.debug("PUT {} -> {} {}".format(
            url, r.status_code, json_response))
    except (ConnectionError):
        logger.warning('Could not connect to CDMI host {}'.format(url))
    except (JSONDecodeError):
        logger.warning('Error decoding JSON from CDMI host {}'.format(url))

    return json_response


def _query_cdmi(url, access_token):
    request_kwargs = _request_auth_kwargs(url, access_token)

    json_response = dict()
    try:
        r = requests.get(url, **request_kwargs)
        json_response = r.json()
        logger.debug('GET {} -> {} {}'.format(
            url, r.status_code, json_response))
    except (ConnectionError):
        logger.warning('Could not connect to CDMI host {}'.format(url))
    except (JSONDecodeError):
        logger.warning('Error decoding JSON from CDMI host {}'.format(url))

    return json_response


def put_capabilities_class(site, path, access_token, is_dir, capabilities):
    cdmi_uri = site.site_uri
    url = urljoin(cdmi_uri, path)

    body = {'capabilitiesURI': capabilities}
    response = _update_qos_cdmi(url, access_token, is_dir, body)

    return response


def get_status(site, path, access_token):
    cdmi_uri = site.site_uri
    url = urljoin(cdmi_uri, path)

    status = _query_cdmi(url, access_token)

    return status


def get_capabilities_class(url, access_token, classes=None):
    capabilities = _query_cdmi(url, access_token)

    capabilities_class = dict()
    try:
        name = capabilities['objectName']
        copies = capabilities['metadata']['cdmi_data_redundancy']
        latency = capabilities['metadata']['cdmi_latency']
        location = capabilities['metadata']['cdmi_geographic_placement']
        transitions = capabilities['metadata']['cdmi_capabilities_allowed']
        transitions = [x.rsplit('/', 1)[-1] for x in transitions]

        qos = [storage_type
               for storage_type, predicate in settings.STORAGE_TYPES
               if predicate(capabilities)]

        capabilities_class = dict(
            metadata=capabilities['metadata'],
            name=name, latency=latency, copies=copies, location=location,
            storage_types=qos, transitions=transitions, url=url)

        logger.debug('QoS for {}: {}'.format(name, qos))

    except (KeyError):
        logger.warning('Wrong or missing CDMI capabilities at {}'.format(url))

    return capabilities_class


def get_all_capabilities(url, access_token):
    capabilities_url = urljoin(url, 'cdmi_capabilities/dataobject')
    capabilities = _query_cdmi(capabilities_url, access_token)

    all_capabilities = []
    try:
        for child in capabilities['children']:
            child_url = urljoin(
                url, 'cdmi_capabilities/dataobject/{}'.format(child))

            capabilities_class = get_capabilities_class(
                child_url, access_token)

            all_capabilities.append(capabilities_class)
    except (KeyError):
        logger.warning('Key error for {}'.format(url))

    return all_capabilities


class ObjectDeletedError(Exception):
    pass


class FileObject(object):
    def __init__(self, name, status):
        self.name = name

        try:
            type = status['objectType']
            cap = status['capabilitiesURI']
        except KeyError:
            logger.warning('Key error for {}'.format(name))
            type = None
            cap = None

        if cap == '/cdmi_capabilities/container' \
           or cap == '/cdmi_capabilities/dataobject':
            raise ObjectDeletedError

        if type == 'application/cdmi-object':
            self.type = 'File'
        elif type == 'application/cdmi-container':
            self.type = 'Directory'

        capabilities_uri = status.get('capabilitiesURI', '')
        metadata = status['metadata']

        self.capabilities_name = capabilities_uri.rsplit('/', 1)[-1]
        self.capabilities_latency = metadata.get('cdmi_latency_provided', '')
        self.capabilities_redundancy = metadata.get('cdmi_data_redundancy_provided', '')
        self.capabilities_geolocation = metadata.get('cdmi_geographic_placement_provided', '')
        self.capabilities_storage_lifetime = metadata.get('cdmi_data_storage_lifetime_provided', '')
        self.capabilities_association_time = metadata.get('cdmi_capability_association_time', '')
        self.capabilities_throughput = metadata.get('cdmi_throughput_provided', '')
        self.capabilities_allowed = metadata.get('cdmi_capabilities_allowed_provided', '')
        self.capabilities_lifetime = metadata.get('cdmi_capability_lifetime_provided', '')
        self.capabilities_lifetime_action = metadata.get('cdmi_capability_lifetime_action_provided', '')
        self.capabilities_target = metadata.get('cdmi_capabilities_target',  '')
        self.capabilities_polling = metadata.get('cdmi_recommended_polling_interval', '')


def list_objects(site, path, access_token):
    url = urljoin(site.site_uri, path)
    try:
        children = _query_cdmi(url, access_token)['children']
    except KeyError:
        logger.warning('Key error for {}'.format(url))
        children = []

    object_list = []
    for child in children:
        child_url = urljoin(url+'/', child)
        try:
            object_list.append(FileObject(
                child, _query_cdmi(child_url, access_token)))
        except ObjectDeletedError:
            logger.warning('{} returned non-existent object {}'.format(
                site.site_uri, child))

    logger.debug('Found objects: {}'.format(object_list))

    return object_list
