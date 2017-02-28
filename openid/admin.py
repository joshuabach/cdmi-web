from django.contrib import admin

from requests.compat import urljoin

from .models import Provider


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):

    fields = ('client_name', 'client_id', 'client_secret',
              'provider_name', 'provider_uri', 'logo_uri')

    def save_model(self, request, obj, form, change):
        obj.from_wellknown_configuration()
        obj.redirect_uri = urljoin(request.scheme + '://' + request.get_host(), 'openid')
        super(ProviderAdmin, self).save_model(request, obj, form, change)
