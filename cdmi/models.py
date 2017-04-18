import os
import shutil

from django.db import models
from django.core.files import storage
from django.urls import reverse


class CantBrowseSite(Exception):
    def __init__(self, site):
        self.site = site


class FileSystemStorage(storage.FileSystemStorage):
    def mkdir(self, name):
        os.makedirs(os.path.join(self.location, name), exist_ok=True)

    def delete(self, name):
        try:
            super().delete(name)
        except IsADirectoryError:
            # https://code.djangoproject.com/ticket/27836
            shutil.rmtree(self.path(name))


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

    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.site_name

    @property
    def can_browse(self):
        return self.browser_path != ''

    @property
    def storage(self):
        if self.can_browse:
            return FileSystemStorage(
                location=self.browser_path,
                base_url=reverse('cdmi:browse', args=[self.id, '']))
        else:
            raise CantBrowseSite(self)


class StorageType(models.Model):
    type_name = models.CharField(max_length=200)
    logo_uri = models.URLField(blank=True)

    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.site_name
