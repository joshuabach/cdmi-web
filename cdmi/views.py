import os
import logging
import re

from requests.compat import urlsplit

from django.shortcuts import redirect
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.sessions.models import Session

from webdav.connection import NotConnection, RemoteParentNotFound

from .models import Site
from . import cdmi, browser
from .cdmi import CdmiError

logger = logging.getLogger(__name__)


def true_path(apparent_path, site, user):
    if site.can_browse:
        prefix = os.path.join(site.root_container, user.username)
    else:
        prefix = site.root_container

    return os.path.join(prefix, re.sub('^/', '', apparent_path))


def has_access_token(user):
    for session in Session.objects.all():
        data = session.get_decoded()
        if '_auth_user_id' in data and int(data['_auth_user_id']) == user.id:
            return 'access_token' in data

    return False


def handle_update_object(request, site, path):
    qos = request.POST['qos']
    capabilities = urlsplit(qos).path

    response = cdmi.put_capabilities_class(
        site, path, request.session['access_token'],
        request.POST['type'] == 'Directory',
        capabilities)

    logger.debug(response)

    return response


@user_passes_test(has_access_token)
def object_info(request, site, path):
    # Basically, this is a CDMI proxy for the jQuery
    site = Site.objects.get(id=site)
    path = re.sub('/+', '/', path)
    cdmi_path = path
    if not path.startswith('/cdmi_'):
        cdmi_path = true_path(path, site, request.user)

    try:
        object_info = cdmi.get_status(
            site, cdmi_path, request.session['access_token'])
    except CdmiError as e:
        logger.warning('{}: {}'.format(e.dict.get('url', site.site_uri), e.dict['msg']))

        return JsonResponse({
            'error': e.dict['msg'],
            'site': site.site_uri,
            'url': e.dict['url']
        })
    else:
        return JsonResponse(object_info)


@csrf_exempt
@user_passes_test(has_access_token)
def update(request, site, path):
    site = Site.objects.get(id=site)
    path = re.sub('/+', '/', path)
    cdmi_path = true_path(path, site, request.user)

    if request.method == 'POST':
        if 'qos' in request.POST and 'type' in request.POST:
            logger.debug("Change {} to {}".format(
                cdmi_path, request.POST['qos']))
            response = handle_update_object(request, site, cdmi_path)
            return JsonResponse(response, status=200)
        else:
            return JsonResponse({'missing_parameters': ['qos', 'type']},
                                status=400)
    else:
        return JsonResponse({'message': 'Use POST'}, status=405)


@user_passes_test(has_access_token)
def delete(request, site, path):
    site = Site.objects.get(id=site)
    path = re.sub('/+', '/', path)
    cdmi_path = true_path(path, site, request.user)

    if request.method == 'POST' and 'name' in request.POST and site.can_browse:
        browser.handle_delete_object(
            site,
            request.POST['name'],
            cdmi_path,
            request.session['access_token'])

        messages.success(request, '{} deleted'.format(
            request.POST['name']))

    if request.method == 'POST' and 'next' in request.POST:
        return redirect(request.POST['next'])
    else:
        return redirect('cdmi:browse', site.id, path)


@user_passes_test(has_access_token)
def upload(request, site, path):
    site = Site.objects.get(id=site)
    path = re.sub('/+', '/', path)
    cdmi_path = true_path(path, site, request.user)

    if request.method == 'POST' and 'file' in request.FILES and site.can_browse:
        browser.handle_uploaded_file(
            site,
            request.FILES['file'],
            cdmi_path,
            request.session['access_token'])

        messages.success(request, '{} uploaded'.format(
            request.FILES['file'].name))

    if request.method == 'POST' and 'next' in request.POST:
        return redirect(request.POST['next'])
    else:
        return redirect('cdmi:browse', site.id, path)


@user_passes_test(has_access_token)
def mkdir(request, site, path):
    site = Site.objects.get(id=site)
    path = re.sub('/+', '/', path)
    cdmi_path = true_path(path, site, request.user)

    if request.method == 'POST' and 'name' in request.POST and site.can_browse:
        browser.handle_create_directory(
            site,
            request.POST['name'],
            cdmi_path,
            request.session['access_token'])

        messages.success(request, '{}/{} created'.format(
            path, request.POST['name']))

    if request.method == 'POST' and 'next' in request.POST:
        return redirect(request.POST['next'])
    else:
        return redirect('cdmi:browse', site.id, path)


class CdmiWebView(UserPassesTestMixin, generic.TemplateView):
    redirect_field_name = 'next'

    def test_func(self):
        return has_access_token(self.request.user)


class BrowserView(CdmiWebView):
    template_name = 'cdmi/browse.html'

    def dispatch(self, request, site, path):
        if site:
            self.site = Site.objects.get(id=site)
        else:
            self.site = Site.objects.get(default=True)

        # Remove leading '/', replace multiple slashes
        clean_path = re.sub('/+', '/', path).lstrip('/')
        if clean_path == path:
            self.path = path
            return super().dispatch(request, site, path)
        else:
            return redirect('cdmi:browse', site, clean_path)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        path = true_path(self.path, self.site, self.request.user)

        logger.debug("Browsing path '{}'".format(path))

        try:
            if self.site.can_browse:
                browser.handle_create_directory(
                    self.site, os.path.join(self.site.root_container, self.request.user.username), '',
                    self.request.session['access_token'])

            context['object_list'] = cdmi.list_objects(
                self.request,
                self.site, path, self.request.session['access_token'])
        except (ConnectionError, NotConnection, RemoteParentNotFound) as e:
            msg = '{}: {}'.format(self.site.site_uri, str(e))

            logger.warning(msg)
            messages.error(self.request, msg)

        except CdmiError as e:
            msg = '{}: {}'.format(e.dict.get('url', self.site.site_uri), e.dict['msg'])

            logger.warning(msg)
            messages.error(self.request, msg)

        return context


class IndexView(CdmiWebView):
    template_name = 'cdmi/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['sites'] = Site.objects.all()

        context['qualities_of_service'] = []
        for site in context['sites']:
            try:
                site.root_container = cdmi.get_status(
                    site, '/',
                    self.request.session['access_token'])
            except (ConnectionError, CdmiError) as e:
                msg = '{}: {}'.format(e.dict.get('url', site.site_uri), e.dict['msg'])

                logger.warning(msg)
                messages.warning(self.request, msg)

            try:
                qoses = cdmi.get_all_capabilities(
                    site.site_uri,
                    self.request.session['access_token'])
            except (ConnectionError, CdmiError) as e:
                msg = '{}: {}'.format(e.dict.get('url', site.site_uri), e.dict['msg'])

                logger.warning(msg)
                messages.error(self.request, msg)
            else:
                for qos in qoses:
                    qos['site'] = site

                context['qualities_of_service'] += qoses

        return context
