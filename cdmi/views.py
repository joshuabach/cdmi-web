import os
import logging
import requests
import shutil

from requests.compat import urljoin, urlsplit

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

    try:
        storage.delete(storage_path)
    except IsADirectoryError:
        # https://code.djangoproject.com/ticket/27836
        shutil.rmtree(storage.path(storage_path))


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


def handle_create_directory(request):
    path = request.POST['path']
    name = request.POST['name']

    new_dir = os.path.join(user_path(request), path, name)
    os_path = os.path.join(settings.MEDIA_ROOT, new_dir)

    logger.debug("Create directory {}".format(os_path))

    os.makedirs(os_path, exist_ok=True)


def handle_update_object(request):
    path = request.POST['path']
    qos = request.POST['qos']
    capabilities = urlsplit(qos).path

    response = cdmi.put_capabilities_class(path, request, capabilities)

    logger.debug(response)

@login_required(login_url='/openid/login')
def update(request):
    if request.method == 'POST':
        if 'qos' in request.POST and 'path' in request.POST:
            logger.debug("Change {} to {}".format(request.POST['path'], request.POST['qos']))
            handle_update_object(request)
            messages.success(request, '{} updated'.format(request.POST['path']))

    if request.method == 'POST' and 'next' in request.POST:
        return redirect(request.POST['next'])
    else:
        return redirect('cdmi:browse')

@login_required(login_url='/openid/login')
def delete(request):
    if request.method == 'POST':
        if 'path' in request.POST and 'name' in request.POST:
            handle_delete_object(request)
            messages.success(request, '{} deleted'.format(request.POST['name']))

    if request.method == 'POST' and 'next' in request.POST:
        return redirect(request.POST['next'])
    else:
        return redirect('cdmi:browse')

@login_required(login_url='/openid/login')
def upload(request):
    if request.method == 'POST':
        if 'file' in request.FILES and 'path' in request.POST:
            handle_uploaded_file(request)
            messages.success(request, '{} uploaded'.format(request.FILES['file'].name))

    if request.method == 'POST' and 'next' in request.POST:
        return redirect(request.POST['next'])
    else:
        return redirect('cdmi:browse')


@login_required(login_url='/openid/login')
def mkdir(request):
    if request.method == 'POST':
        if 'path' in request.POST and 'name' in request.POST:
            handle_create_directory(request)
            messages.success(request, '{}/{} created'.format(
                request.POST['path'], request.POST['name']))

    if request.method == 'POST' and 'next' in request.POST:
        return redirect(request.POST['next'])
    else:
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
    o.capabilities_target = metadata.get('cdmi_capabilities_target', '')
    o.capabilities_polling = metadata.get('cdmi_recommended_polling_interval','')

    return o

@login_required(login_url='/openid/login')
def browse(request):
    username = request.user.username
    storage_path = user_path(request)
    create_if_not_exists(storage_path)
    path = storage_path

    context = dict()

    if 'chdir' in request.GET:
        if 'path' in request.GET and 'name' in request.GET:
            path = os.path.join(path, request.GET['path'], request.GET['name'])

    object_info = None
    if 'info' in request.GET:
        if 'path' in request.GET and 'name' in request.GET:
            path = os.path.join(path, request.GET['path'])
            url = urljoin(settings.CDMI_URI, request.GET['info'])
            object_info = cdmi.get_capabilities_class(url, request)
            object_info['url'] = url
            object_info['path'] = os.path.join(path, request.GET['name'])
            context['next_url'] = request.GET['nextbutone']

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

    context.update({
            'object_list': object_list,
            'username': username,
            'path': os.path.relpath(path, storage_path),
            'object_info': object_info
        })

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
        context['username'] = self.request.user.username
        context['filters'] = [f for f, _ in settings.STORAGE_TYPES]

        return context
