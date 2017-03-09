import os
import logging
import shutil

from django.conf import settings
from django.core.files.storage import default_storage


logger = logging.getLogger(__name__)
storage = default_storage


def user_path(request):
    return os.path.join('', request.user.username)


def create_if_not_exists(path):
    path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(path):
        os.makedirs(path)


class FileObject(object):
    def __init__(self, name, type, path=''):
        self.name = name
        self.type = type


def handle_delete_object(request):
    name = request.POST['name']
    path = request.POST['path']

    storage_path = os.path.join(user_path(request), path, name)

    logger.debug("Delete {}".format(storage_path))

    try:
        storage.delete(storage_path)
    except IsADirectoryError:
        # https://code.djangoproject.com/ticket/27836
        shutil.rmtree(storage.path(storage_path))


def handle_uploaded_file(request):
    f = request.FILES['file']
    path = request.POST['path']
    name = f.name

    storage_path = os.path.join(user_path(request), path, name)
    os_path = os.path.join(settings.MEDIA_ROOT, storage_path)

    logger.debug("Upload {}".format(os_path))

    with open(os_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def handle_create_directory(request):
    path = request.POST['path']
    name = request.POST['name']

    new_dir = os.path.join(user_path(request), path, name)
    os_path = os.path.join(settings.MEDIA_ROOT, new_dir)

    logger.debug("Create directory {}".format(os_path))

    os.makedirs(os_path, exist_ok=True)


def list_objects(path):
    dirs, files = storage.listdir(path)
    object_list = []

    for d in dirs:
        o = FileObject(d, 'Directory')

        object_list.append(o)

    for f in files:
        o = FileObject(f, 'File')

        object_list.append(o)

    return object_list
