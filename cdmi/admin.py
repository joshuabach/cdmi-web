from django.contrib import admin

from .models import Site, WebDAVServer

admin.site.register(Site)
admin.site.register(WebDAVServer)
