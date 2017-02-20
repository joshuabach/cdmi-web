from django.db import models

import requests
from requests.compat import urljoin

class Provider(models.Model):
    client_name = models.CharField(max_length=200, blank=True)
    client_id = models.CharField(max_length=200, blank=True)
    client_secret = models.CharField(max_length=200, blank=True)
    redirect_uri = models.URLField(blank=True)

    authorization_endpoint = models.URLField()
    introspection_endpoint = models.URLField(blank=True)
    token_endpoint = models.URLField()
    jwks_uri = models.URLField()
    userinfo_endpoint = models.URLField()

    provider_name = models.CharField(max_length=200)
    provider_uri = models.URLField()
    logo_uri = models.URLField(blank=True)
    openid_configuration = models.TextField(blank=True)

    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.provider_name

    def from_wellknown_configuration(self):
        url = urljoin(self.provider_uri, '.well-known/openid-configuration')
        r = requests.get(url)

        conf_json = r.json()

        self.authorization_endpoint = conf_json.get('authorization_endpoint', '')
        self.introspection_endpoint = conf_json.get('introspection_endpoint', '')
        self.token_endpoint = conf_json.get('token_endpoint', '')
        self.jwks_uri = conf_json.get('jwks_uri', '')
        self.userinfo_endpoint = conf_json.get('userinfo_endpoint', '')
        self.openid_configuration = conf_json

        self.save()
