import os
import logging

from requests.compat import urljoin, urlsplit

from django.shortcuts import render, redirect
from django.views import generic
from django.conf import settings
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
        logger.debug(data)
        if '_auth_user_id' in data and int(data['_auth_user_id']) == user.id:
            logger.debug("{} for {}:{} with session {}".format(
                'Succeeding' if 'access_token' in data else 'Failing',
                user.id, user.username, data))

            return 'access_token' in data

    logger.debug("No session found for {}:{}".format(user.id, user.username))
    return False


def handle_update_object(request, site, path):
    qos = request.POST['qos']
    capabilities = urlsplit(qos).path

    response = cdmi.put_capabilities_class(
        site, path, request.session['access_token'],
        'is_dir' in request.POST and request.POST['is_dir'] == 'True',
        capabilities)

    logger.debug(response)


@user_passes_test(has_access_token, login_url='/openid/login/')
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


@user_passes_test(has_access_token, login_url='/openid/login/')
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


@user_passes_test(has_access_token, login_url='/openid/login/')
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


@user_passes_test(has_access_token, login_url='/openid/login/')
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


@user_passes_test(has_access_token, login_url='/openid/login/')
def browse(request, site, path):
    site = Site.objects.get(id=site)

    username = request.user.username

    context = dict()

    object_info = None
    if 'info' in request.GET and 'name' in request.GET:
        url = urljoin(site.site_uri, request.GET['info'])
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

    object_list = cdmi.list_objects(site, path, request.session['access_token'])

    context.update({
            'object_list': object_list,
            'username': username,
            'path': path,
            'site': site,
            'object_info': object_info
        })

    return render(request, 'cdmi/browse.html', context)


class IndexView(UserPassesTestMixin, generic.ListView):
    template_name = 'cdmi/index.html'
    login_url = '/openid/login/'
    redirect_field_name = 'next'

    model = Site

    context_object_name = 'storage_list'

    def test_func(self):
        return has_access_token(self.request.user)

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
