import json
import requests
import logging

from requests.compat import urljoin
from requests.exceptions import ConnectionError
from django.contrib import messages
from django.conf import settings

logger = logging.getLogger(__name__)

def get_status(request, fileobject):
    cdmi_uri = settings.CDMI_URI
    #access_token = request.session['access_token']
    #headers = {'Authorization': 'Bearer {}'.format(access_token)}

    username = request.user.username

    url = urljoin(cdmi_uri, '{}/{}'.format(username, fileobject))

    status = dict()
    try:
        r = requests.get(url, auth=('restadmin', 'restadmin')) # headers=headers)
        status = r.json()

        logger.debug(status)
    except (ConnectionError):
        logger.warning('Could not connect to CDMI host {}'.format(cdmi_uri))

    return status

#  def get_status(request, fileobjects):
#      try:
#          cdmi_uri = settings.CDMI_URI
#      except (AttributeError):
#          messages.warning(request, 'No CDMI server configured.')
#          return
#      try:
#          access_token = request.session['access_token']
#      except (KeyError):
#          messages.warning(request, 'No valid access token for this session.')
#          return
#
#      username = request.user.username
#
#      for fileobject in fileobjects:
#
#          headers = {'Authorization': 'Bearer {}'.format(access_token)}
#
#          url = urljoin(cdmi_uri, '{}/{}'.format(username, fileobject.filename))
#
#          r = requests.get(url, headers=headers)
#          status = r.json()
#
#          messages.info(request, json.dumps(status, indent=4))
