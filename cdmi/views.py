import os
import logging

from requests.compat import urljoin, urlsplit

from django.shortcuts import render, redirect
from django.views import generic
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin


from .models import Site
from . import cdmi, browser

logger = logging.getLogger(__name__)


def handle_update_object(request, site, path):
    qos = request.POST['qos']
    capabilities = urlsplit(qos).path

    response = cdmi.put_capabilities_class(
        site, path, request.session['access_token'],
        'is_dir' in request.POST and request.POST['is_dir'] == 'True',
        capabilities)

    logger.debug(response)


@login_required(login_url='/openid/login')
def update(request, site, path):
    site = Site.objects.get(id=site)

    if request.method == 'POST':
        if 'qos' in request.POST:
            logger.debug("Change {} to {}".format(
                path, request.POST['qos']))
            handle_update_object(request, site, path)
            messages.success(request, '{} updated'.format(
                path))

    if request.method == 'POST' and 'next' in request.POST:
        return redirect(request.POST['next'])
    else:
        return redirect('cdmi:browse', site.id, path)


@login_required(login_url='/openid/login')
def delete(request, site, path):
    site = Site.objects.get(id=site)

    if request.method == 'POST':
        if 'name' in request.POST:
            if site.browser_module == 'browser':
                browser.handle_delete_object(request.POST['name'],
                                             path)

                messages.success(request, '{} deleted'.format(
                    request.POST['name']))

    if request.method == 'POST' and 'next' in request.POST:
        return redirect(request.POST['next'])
    else:
        return redirect('cdmi:browse', site.id, path)


@login_required(login_url='/openid/login')
def upload(request, site, path):
    site = Site.objects.get(id=site)
    if request.method == 'POST':
        if 'file' in request.FILES:
            if site.browser_module == 'browser':
                browser.handle_uploaded_file(request.FILES['file'],
                                             path)
                messages.success(request, '{} uploaded'.format(
                    request.FILES['file'].name))

    if request.method == 'POST' and 'next' in request.POST:
        return redirect(request.POST['next'])
    else:
        return redirect('cdmi:browse', site.id, path)


@login_required(login_url='/openid/login')
def mkdir(request, site, path):
    site = Site.objects.get(id=site)

    if request.method == 'POST':
        if 'name' in request.POST:
            if site.browser_module == 'browser':
                browser.handle_create_directory(request.POST['name'],
                                                path)
                messages.success(request, '{}/{} created'.format(
                    path, request.POST['name']))

    if request.method == 'POST' and 'next' in request.POST:
        return redirect(request.POST['next'])
    else:
        return redirect('cdmi:browse', site.id, path)


def _set_object_capabilities(o, status):
    capabilities_uri = status.get('capabilitiesURI', '')
    metadata = status['metadata']

    o.capabilities_name = capabilities_uri.rsplit('/', 1)[-1]
    o.capabilities_latency = metadata.get('cdmi_latency_provided', '')
    o.capabilities_redundancy = metadata.get('cdmi_data_redundancy_provided', '')
    o.capabilities_geolocation = metadata.get('cdmi_geographic_placement_provided', '')
    o.capabilities_storage_lifetime = metadata.get('cdmi_data_storage_lifetime_provided', '')
    o.capabilities_association_time = metadata.get('cdmi_capability_association_time', '')
    o.capabilities_throughput = metadata.get('cdmi_throughput_provided', '')
    o.capabilities_allowed = metadata.get('cdmi_capabilities_allowed_provided', '')
    o.capabilities_lifetime = metadata.get('cdmi_capability_lifetime_provided', '')
    o.capabilities_lifetime_action = metadata.get('cdmi_capability_lifetime_action_provided', '')
    o.capabilities_target = metadata.get('cdmi_capabilities_target',  '')
    o.capabilities_polling = metadata.get('cdmi_recommended_polling_interval', '')

    return o


@login_required(login_url='/openid/login')
def browse(request, site, path):
    site = Site.objects.get(id=site)

    username = request.user.username

    context = dict()

    object_info = None
    if 'info' in request.GET and 'name' in request.GET:
        url = urljoin(settings.CDMI_URI, request.GET['info'])
        object_info = cdmi.get_capabilities_class(
            url, request.session['access_token'])
        object_info['url'] = url
        object_info['path'] = os.path.join(path, request.GET['name'])
        abs_path = os.path.join(settings.MEDIA_ROOT, path,
                                request.GET['name'])
        object_info['is_dir'] = os.path.isdir(abs_path)

        logger.debug("Is dir? {} {}".format(
            abs_path, os.path.isdir(abs_path)))

        context['next_url'] = request.GET['nextbutone']

    logger.debug("current path {}".format(path))

    object_list = [
        _set_object_capabilities(
            obj, cdmi.get_status(site, os.path.join(path, obj.name),
                                 request.session['access_token']))
        for obj in browser.list_objects(path)]

    context.update({
            'object_list': object_list,
            'username': username,
            'path': path,
            'site': site,
            'object_info': object_info
        })

    return render(request, 'cdmi/browse.html', context)


class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'cdmi/index.html'
    login_url = '/openid/login'
    redirect_field_name = ''

    model = Site

    context_object_name = 'storage_list'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['username'] = self.request.user.username
        context['sites'] = Site.objects.all()

        context['qualities_of_service'] = []
        for site in Site.objects.all():
            context['qualities_of_service'] += cdmi.get_all_capabilities(
                site.site_uri,
                self.request.session['access_token'])

        return context
