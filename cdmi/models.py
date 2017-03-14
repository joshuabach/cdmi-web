from django.db import models
from django.core.files.storage import FileSystemStorage
from django.urls import reverse


class CantBrowseSite(Exception):
    def __init__(self, site):
        self.site = site


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
