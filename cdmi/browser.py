import os
import logging

from django.conf import settings
from django.core.files.storage import DefaultStorage

from filebrowser.sites import FileBrowserSite

logger = logging.getLogger(__name__)

class CdmiFileBrowserSite(FileBrowserSite):

    def _set_user_directory(self, request):
        username = request.user.username
        logger.debug("user: {}".format(username))
        path = username # os.path.join(settings.MEDIA_ROOT, subject)
        if not self.storage.exists(path):
            self.storage.makedirs(path)

        logger.debug("set directory {}/".format(path))
        self.directory = '{}/'.format(path)

    def browse(self, request):
        self._set_user_directory(request)
        return super().browse(request)

    def createdir(self, request):
        self._set_user_directory(request)
        return super().createdir(request)

    def upload(self, request):
        self._set_user_directory(request)
        return super().upload(request)

    def delete_confirm(self, request):
        self._set_user_directory(request)
        return super().delete_confirm(request)

    def delete(self, request):
        self._set_user_directory(request)
        return super().delete(request)

    def detail(self, request):
        self._set_user_directory(request)
        return super().detail(request)

    def version(self, request):
        self._set_user_directory(request)
        return super().version(request)

    def _upload_file(self, request):
        self._set_user_directory(request)
        return super()._upload_file(request)

#site = FileBrowserSite(name='filebrowser', storage=storage)
storage = DefaultStorage()
site = CdmiFileBrowserSite(name='cdmifilebrowser', storage=storage)

from .cdmi import get_status

get_status.short_description = 'CDMI status'
site.add_action(get_status)
