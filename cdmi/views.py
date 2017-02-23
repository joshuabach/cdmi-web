import os
import logging
import requests

from requests.compat import urljoin

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import generic
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.contrib import messages

from .models import Site, StorageType
from .cdmi import get_status

logger = logging.getLogger(__name__)
storage = default_storage

def user_path(request):
    return os.path.join('', request.user.username)

def create_if_not_exists(path):
    path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(path):
        os.makedirs(path)

class FileObject(object):
    def __init__(self, name, type, path=''):
        self.name = name
        self.type = type

def handle_delete_object(request):
    name = request.POST['name']
    path = request.POST['path']
    
    storage_path = os.path.join(user_path(request), path, name)

    logger.debug("Delete {}".format(storage_path))

    storage.delete(storage_path)

def handle_uploaded_file(request):
    f = request.FILES['file']
    path = request.POST['path']
    name = f.name

    storage_path = os.path.join(user_path(request), path, name)
    os_path = os.path.join(settings.MEDIA_ROOT, storage_path)

    logger.debug("Upload {}".format(os_path))

    with open(os_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

@login_required(login_url='/openid/login')
def delete(request):
    if request.method == 'POST':
        if 'path' in request.POST and 'name' in request.POST:
            handle_delete_object(request)
            messages.success(request, '{} deleted'.format(request.POST['name']))

    return redirect('cdmi:browse')

@login_required(login_url='/openid/login')
def upload(request):
    if request.method == 'POST':
        if 'file' in request.FILES and 'path' in request.POST:
            handle_uploaded_file(request)
            messages.success(request, '{} uploaded'.format(request.FILES['file'].name))

    return redirect('cdmi:browse')

@login_required(login_url='/openid/login')
def browse(request):
    username = request.user.username
    storage_path = user_path(request)
    create_if_not_exists(storage_path)
    path = storage_path

    if 'path' in request.GET and 'name' in request.GET:
        path = os.path.join(path, request.GET['path'], request.GET['name'])

    logger.debug("current path {}".format(path))

    dirs, files = storage.listdir(path)
    object_list = []

    for d in dirs:
        o = FileObject(d, 'Directory')
        p = os.path.join(path, d)
        cdmi_status = get_status(p)

        capabilities_uri = cdmi_status.get('capabilitiesURI', '')
        o.capabilities_name = capabilities_uri.rsplit('/', 1)[-1]
        o.capabilities_latency = cdmi_status['metadata'].get('cdmi_latency_provided','')
        o.capabilities_redundancy = cdmi_status['metadata'].get('cdmi_data_redundancy_provided','')
        o.capabilities_geolocation = cdmi_status['metadata'].get('cdmi_geographic_placement_provided','')
        object_list.append(o)
    
    for f in files:
        o = FileObject(f, 'File')
        p = os.path.join(path, f)
        cdmi_status = get_status(p)

        capabilities_uri = cdmi_status.get('capabilitiesURI', '')
        o.capabilities_name = capabilities_uri.rsplit('/', 1)[-1]
        o.capabilities_latency = cdmi_status['metadata'].get('cdmi_latency_provided','')
        o.capabilities_redundancy = cdmi_status['metadata'].get('cdmi_data_redundancy_provided','')
        o.capabilities_geolocation = cdmi_status['metadata'].get('cdmi_geographic_placement_provided','')
        object_list.append(o)

    context = {
            'object_list': object_list,
            'username': username,
            'path': os.path.relpath(path, storage_path)
        }

    return render(request, 'cdmi/browse.html', context)

@csrf_exempt
def sites(request):
    filter = request.GET.get('filter', '')

    json_response = dict()

    all_sites = []

    for site in Site.objects.all():
        url = urljoin(site.site_uri, 'cdmi_capabilities/dataobject')
        try:
            r = requests.get(url, auth=('restadmin','restadmin'))
            logger.debug(r.json())
        except (requests.exceptions.ConnectionError):
            logger.warning("Could not connect to {}".format(url))
            break 
        if r.status_code == 200:
            capabilities = r.json()
            try:
                for child in capabilities['children']:
                    url = urljoin(site.site_uri, 'cdmi_capabilities/dataobject/{}'.format(child))
                    r = requests.get(url, auth=('restadmin','restadmin'))
                    logger.debug(r.json())
                    if r.status_code == 200:
                        profile = r.json()
                        copies = profile['metadata']['cdmi_data_redundancy']
                        latency = profile['metadata']['cdmi_latency']
                        location = profile['metadata']['cdmi_geographic_placement']
                        transitions = profile['metadata']['cdmi_capabilities_allowed']
                        transitions = [ x.rsplit('/', 1)[-1] for x in transitions ]

                        datapath = 'http://localhost:8000/cdmi/browse'

                        qos_profile = dict(name=child, latency=latency, copies=copies, location=location,
                                qos=[], transitions=transitions, url=url, datapath=datapath)


                        if int(latency) < 200:
                            qos_profile['qos'].append('processing')
                        if int(copies) > 3:
                            qos_profile['qos'].append('archiving')

                        all_sites.append(qos_profile)
            except (KeyError):
                logger.warning('error for {}'.format(url))

    if filter == 'processing':
        json_response['sites'] = [x for x in all_sites if 'processing' in x['qos']]

    if filter == 'archiving':
        json_response['sites'] = [x for x in all_sites if 'archiving' in x['qos']]

    return JsonResponse(json_response)

class IndexView(generic.ListView):
    template_name = 'cdmi/index.html'

    context_object_name = 'storage_list'
