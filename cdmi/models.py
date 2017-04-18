import os
import shutil
import tempfile
import logging

from django.db import models
from django.core.files import storage
from django.urls import reverse

import webdav.client as webdav


logger = logging.getLogger(__name__)


class FileSystemStorage(storage.FileSystemStorage):
    def mkdir(self, name):
        os.makedirs(os.path.join(self.location, name), exist_ok=True)

    def delete(self, name):
        try:
            super().delete(name)
        except IsADirectoryError:
            # https://code.djangoproject.com/ticket/27836
            shutil.rmtree(self.path(name))


class WebDAVServer(models.Model, storage.Storage):
    hostname = models.URLField()
    login = models.CharField(max_length=200)
    passwd = models.CharField(max_length=200)

    def __str__(self):
        return self.hostname

    def ensure_connected(self):
        if not hasattr(self, 'connection'):
            options = {
                'webdav_hostname': self.hostname,
                'webdav_login': self.login,
                'webdav_password': self.passwd,
            }

            logger.debug("WebDAV: Connecting to {}".format(options))
            self.connection = webdav.Client(options)

    def delete(self, name):
        self.ensure_connected()
        self.connection.clean(name)

    def exists(self, name):
        self.ensure_connected()
        self.connection.check(name)

    def listdir(self, path):
        self.ensure_connected()
        self.connection.list(path)

    def open(self, name, mode='rb'):
        self.ensure_connected()
        tmp = tempfile.NamedTemporaryFile()
        self.connection.download_sync(
            remote_path=name,
            local_path=tmp.name)

        tmp.seek(0)
        return tmp

    def save(self, name, content, max_length=None):
        self.ensure_connected()
        tmp = tempfile.NamedTemporaryFile()
        tmp.write(content.read())

        self.connection.upload_sync(
            remote_path=name,
            local_path=tmp.name)

    def mkdir(self, name):
        self.ensure_connected()
        self.connection.mkdir(name)


class Site(models.Model):
    site_name = models.CharField(max_length=200)
    site_uri = models.URLField()
    logo_uri = models.URLField(blank=True)
    auth = models.CharField(
        default='bearer',
        choices=[
            ('bearer', 'Bearer token authentication'),
            # Useful for testing
            ('basic', 'HTTP basic authentication with restadmin:restadmin')],
        max_length=10)
    browser_path = models.CharField(
        blank=True, default='', max_length=128)

    browser_webdav = models.ForeignKey(WebDAVServer,
        null=True, on_delete=models.SET_NULL)

    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.site_name

    @property
    def can_browse(self):
        return hasattr(self, 'storage')

    @property
    def storage(self):
        if self.browser_path:
            return FileSystemStorage(
                location=self.browser_path,
                base_url=reverse('cdmi:browse', args=[self.id, '']))
        elif self.browser_webdav:
            return self.browser_webdav
        else:
            raise AttributeError("'Site' object {} has no attribute 'storage'".format(self))


class StorageType(models.Model):
    type_name = models.CharField(max_length=200)
    logo_uri = models.URLField(blank=True)

    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.site_name
