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
from django.core.files.storage import FileSystemStorage

from .models import Site, StorageType
from .cdmi import get_status
from .forms import UploadFileForm

logger = logging.getLogger(__name__)

def handle_delete_object(request):
    name = request.POST['file']
    username = request.user.username
    path = os.path.join(settings.MEDIA_ROOT, username, name)

    logger.debug("Delete {}".format(path))
    storage = FileSystemStorage(location=path)

    storage.delete(path)

def handle_uploaded_file(request):
    f = request.FILES['file']
    username = request.user.username
    path = os.path.join(settings.MEDIA_ROOT, username, f.name)

    logger.debug("Upload {}".format(path))
    storage = FileSystemStorage(location=path)
    #  with open('some/file/name.txt', 'wb+') as destination:
    #      for chunk in f.chunks():
    #          destination.write(chunk)

    storage.save(path, f)

class FileObject(object):
    def __init__(self, name, type):
        self.name = name
        self.type = type

class IndexView(generic.ListView):
    template_name = 'cdmi/index.html'
    model = StorageType

    context_object_name = 'storage_list'

@login_required(login_url='/openid/login')
def delete(request):
    if request.method == 'POST':
        handle_delete_object(request)
    return redirect('cdmi:browse')

@login_required(login_url='/openid/login')
def upload(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request)
    return redirect('cdmi:browse')

@login_required(login_url='/openid/login')
def browse(request):
    username = request.user.username
    path = os.path.join(settings.MEDIA_ROOT, username)

    storage = FileSystemStorage(location=path)
    logger.debug("current path {}".format(path))

    if not storage.exists(path):
        storage.makedirs(path)

    dirs, files = storage.listdir(path)
    object_list = []

    for d in dirs:
        o = FileObject(d, 'Directory')
        cdmi_status = get_status(request, d)

        capabilities = cdmi_status.get('capabilitiesURI', '')
        o.capabilities = capabilities.rsplit('/', 1)[-1]
        object_list.append(o)
    
    for f in files:
        o = FileObject(f, 'File')
        cdmi_status = get_status(request, f)

        capabilities = cdmi_status.get('capabilitiesURI', '')
        o.capabilities = capabilities.rsplit('/', 1)[-1]
        object_list.append(o)

    context = {
            'object_list': object_list,
            'username': username,
            'form': UploadFileForm()
        }

    return render(request, 'cdmi/browse.html', context)

@csrf_exempt
def sites(request):
    filter = request.GET.get('filter', '')

    json_response = dict()

    all_sites = []

    for site in Site.objects.all():
        url = urljoin(site.site_uri, 'cdmi_capabilities/dataobject')
        r = requests.get(url, auth=('restadmin','restadmin'))
        logger.debug(r.json())
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
