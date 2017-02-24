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
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Site, StorageType
from . import cdmi

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

def _set_object_capabilities(o, status):
    capabilities_uri = status.get('capabilitiesURI', '')
    metadata = status['metadata']

    o.capabilities_name = capabilities_uri.rsplit('/', 1)[-1]
    o.capabilities_latency = metadata.get('cdmi_latency_provided','')
    o.capabilities_redundancy = metadata.get('cdmi_data_redundancy_provided','')
    o.capabilities_geolocation = metadata.get('cdmi_geographic_placement_provided','')
    o.capabilities_storage_lifetime = metadata.get('cdmi_data_storage_lifetime_provided','')
    o.capabilities_association_time = metadata.get('cdmi_capability_association_time','')
    o.capabilities_throughput = metadata.get('cdmi_throughput_provided','')
    o.capabilities_allowed = metadata.get('cdmi_capabilities_allowed_provided','')
    o.capabilities_lifetime = metadata.get('cdmi_capability_lifetime_provided','')
    o.capabilities_lifetime_action = metadata.get('cdmi_capability_lifetime_action_provided','')

    return o

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
        status = cdmi.get_status(p, request)

        object_list.append(_set_object_capabilities(o, status))

    for f in files:
        o = FileObject(f, 'File')
        p = os.path.join(path, f)
        status = cdmi.get_status(p, request)

        object_list.append(_set_object_capabilities(o, status))

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

    all_capabilities = []

    for site in Site.objects.all():
        all_capabilities += cdmi.get_all_capabilities(site.site_uri, request)
        
    if filter == 'processing':
        json_response['sites'] = [x for x in all_capabilities if 'processing' in x['qos']]

    if filter == 'archiving':
        json_response['sites'] = [x for x in all_capabilities if 'archiving' in x['qos']]

    return JsonResponse(json_response)

class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'cdmi/index.html'
    login_url = '/openid/login'
    redirect_field_name = ''

    model = Site

    context_object_name = 'storage_list'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['sites_endpoint'] = settings.SITES_ENDPOINT

        return context
