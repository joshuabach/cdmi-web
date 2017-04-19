import os
import logging
import re

from requests.compat import urljoin, urlsplit

from django.shortcuts import render, redirect
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.sessions.models import Session


from .models import Site
from . import cdmi, browser

logger = logging.getLogger(__name__)


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

    object_info = cdmi.get_status(
        site, path, request.session['access_token'])

    return JsonResponse(object_info)


@csrf_exempt
@user_passes_test(has_access_token)
def update(request, site, path):
    site = Site.objects.get(id=site)
    path = re.sub('/+', '/', path)

    if request.method == 'POST':
        if 'qos' in request.POST and 'type' in request.POST:
            logger.debug("Change {} to {}".format(
                path, request.POST['qos']))
            response = handle_update_object(request, site, path)
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

    if request.method == 'POST' and 'name' in request.POST and site.can_browse:
        browser.handle_delete_object(
            site,
            request.POST['name'],
            path,
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

    if request.method == 'POST' and 'file' in request.FILES and site.can_browse:
        browser.handle_uploaded_file(
            site,
            request.FILES['file'],
            path,
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

    if request.method == 'POST' and 'name' in request.POST and site.can_browse:
        browser.handle_create_directory(
            site,
            request.POST['name'],
            path,
            request.session['access_token'])

        messages.success(request, '{}/{} created'.format(
            path, request.POST['name']))

    if request.method == 'POST' and 'next' in request.POST:
        return redirect(request.POST['next'])
    else:
        return redirect('cdmi:browse', site.id, path)


def browse_default(request, path):
    site = Site.objects.filter(site_uri__contains='localhost')[0]

    return redirect('cdmi:browse', site.id, path)


class CdmiWebView(UserPassesTestMixin, generic.TemplateView):
    redirect_field_name = 'next'

    def test_func(self):
        return has_access_token(self.request.user)


class BrowserView(CdmiWebView):
    template_name = 'cdmi/browse.html'

    def get_context_data(self, **kwargs):
        context = super(BrowserView, self).get_context_data(**kwargs)
        site = Site.objects.get(id=self.kwargs['site'])
        path = re.sub('/+', '/', self.kwargs['path'])

        username = self.request.user.username

        context = dict()

        if site.can_browse:
            if not path.startswith(self.request.user.username):
                path = os.path.join(self.request.user.username, path)
                if path[-1] == '/':
                    path = path[:-1]

            browser.handle_create_directory(site, self.request.user.username, '',
                                            self.request.session['access_token'])

        logger.debug("Browsing path '{}'".format(path))

        try:
            object_list = cdmi.list_objects(site, path, self.request.session['access_token'])
        except ConnectionError:
            logger.warning('Could not connect to CDMI host {}'.format(site.site_uri))
            error = 'Could not connect to {}'.format(site.site_uri)
            object_list = None
        except cdmi.CdmiError as e:
            logger.warning('KeyError when handling response from {}'.format(site))
            error = e.dict
            object_list = None
        else:
            error = None

        context.update({
            'object_list': object_list,
            'username': username,
            'path': path,
            'site': site,
            'error': error
        })

        return context


class IndexView(CdmiWebView):
    template_name = 'cdmi/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['username'] = self.request.user.username
        context['sites'] = Site.objects.all()

        context['qualities_of_service'] = []
        for site in context['sites']:
            try:
                site.root_container = cdmi.get_status(
                    site, '/',
                    self.request.session['access_token'])

                qoses = cdmi.get_all_capabilities(
                    site.site_uri,
                    self.request.session['access_token'])
            except cdmi.CdmiError as e:
                messages.error(self.request,
                               '{}: {}'.format(site.site_uri, e.dict['msg']))
            else:
                for qos in qoses:
                    qos['site'] = site

                context['qualities_of_service'] += qoses

        return context
