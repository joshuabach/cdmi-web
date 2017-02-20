from django.test import TestCase
from django.urls import reverse

from .models import Provider

class ProviderMethodTests(TestCase):

    def test_from_wellknown_configuration(self):
        """
        from_wellknown_configuration() should update the Provider object
        from the .well-known/openid-configuration provider endpoint.
        """
        provider = Provider(provider_uri="https://accounts.google.com")
        provider.from_wellknown_configuration()

        self.assertIsNotNone(provider.authorization_endpoint)
        self.assertIsNotNone(provider.introspection_endpoint)
        self.assertIsNotNone(provider.token_endpoint)
        self.assertIsNotNone(provider.jwks_uri)
        self.assertIsNotNone(provider.userinfo_endpoint)

class ProviderViewTests(TestCase):
    
    def test_login_view_with_no_providers(self):
        """
        """
        response = self.client.get(reverse('openid:login'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['provider_list'], [])
