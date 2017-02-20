import logging

from django.contrib import admin

from .models import Site, StorageType

from filebrowser.settings import ADMIN_THUMBNAIL

logger = logging.getLogger(__name__)

def image_thumbnail(self, obj):
    logger.debug("set thumbnail for {}".format(obj))
    return '<img src="static/filebrowser/img/completed.png" />'

image_thumbnail.allow_tags = True
image_thumbnail.short_description = "Status"

admin.ModelAdmin.image_thumbnail = image_thumbnail

admin.site.register(Site)
admin.site.register(StorageType)
