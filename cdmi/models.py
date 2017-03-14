from django.db import models


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
    browser_module = models.CharField(
        blank=True, default='', max_length=128)

    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.site_name

    @property
    def can_browse(self):
        return self.browser_module != ''


class StorageType(models.Model):
    type_name = models.CharField(max_length=200)
    logo_uri = models.URLField(blank=True)

    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.site_name
