import os
import shutil
import tempfile
import logging

from django.db import models
from django.core.files import storage
from django.urls import reverse
from django.forms import ValidationError

import webdav.client as webdav


logger = logging.getLogger(__name__)


class FileSystemStorage(storage.FileSystemStorage):
    access_type = 'local File system'

    def ensure_connected(self, *args, **kwargs):
        # Nothing needs to be done to connect to the local filesystem
        pass

    def mkdir(self, name):
        os.makedirs(os.path.join(self.location, name), exist_ok=True)

    def delete(self, name):
        try:
            super().delete(name)
        except IsADirectoryError:
            # https://code.djangoproject.com/ticket/27836
            shutil.rmtree(self.path(name))

    def store(self, name, content, max_length=None):
        logger.debug("Try to save file with...")
        logger.debug("location: {}".format(self.location))
        logger.debug("base_url: {}".format(self.base_url))
        logger.debug("name: {}".format(name))
        logger.debug("content: {}".format(str(content)))

        import os
        with open(os.path.join(self.location, name), 'wb') as f:
            f.write(content.file.read())

        #self.save(name, content, max_length)


class WebDAVServer(models.Model, storage.Storage):
    hostname = models.URLField()
    login = models.CharField(max_length=200, blank=True, default='')
    passwd = models.CharField(max_length=200, blank=True, default='')

    access_type = 'WebDAV'

    def __str__(self):
        return self.hostname

    def ensure_connected(self, access_token=None):
        if not hasattr(self, 'connection'):
            options = dict()
            options['webdav_hostname'] = self.hostname
            if self.login and self.passwd:
                options['webdav_login'] = self.login
                options['webdav_password'] = self.passwd
            elif access_token:
                options['webdav_token'] = access_token

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

    def store(self, name, content, max_length=None):
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

    browser_webdav = models.ForeignKey(
        WebDAVServer,
        blank=True, null=True, on_delete=models.SET_NULL)

    root_container = models.CharField(max_length=200, blank=True, default='')

    default = models.BooleanField(default=False)

    last_modified = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.default:
            for site in Site.objects.exclude(pk=self.pk).filter(default=True):
                site.default = False
                site.save()
        elif Site.objects.filter(default=True).count() <= 0:
            raise ValidationError("Exactly one site in the database needs to be marked 'Default'")

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
