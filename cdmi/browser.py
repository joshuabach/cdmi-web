import os
import logging
import shutil

from django.conf import settings
from django.core.files.storage import default_storage


logger = logging.getLogger(__name__)
storage = default_storage


def create_if_not_exists(path):
    path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(path):
        os.makedirs(path)


class FileObject(object):
    def __init__(self, name, type, path=''):
        self.name = name
        self.type = type


def handle_delete_object(name, path):
    storage_path = os.path.join(path, name)

    logger.debug("Delete {}".format(storage_path))

    try:
        storage.delete(storage_path)
    except IsADirectoryError:
        # https://code.djangoproject.com/ticket/27836
        shutil.rmtree(storage.path(storage_path))


def handle_uploaded_file(file, path):
    name = file.name

    storage_path = os.path.join(path, name)
    os_path = os.path.join(settings.MEDIA_ROOT, storage_path)

    logger.debug("Upload {}".format(os_path))

    with open(os_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)


def handle_create_directory(name, path):
    new_dir = os.path.join(path, name)
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
