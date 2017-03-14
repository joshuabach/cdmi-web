import os
import logging
import shutil


logger = logging.getLogger(__name__)


def handle_delete_object(site, name, path):
    storage_path = os.path.join(path, name)

    logger.debug("Delete {}".format(storage_path))

    try:
        site.storage.delete(storage_path)
    except IsADirectoryError:
        # https://code.djangoproject.com/ticket/27836
        shutil.rmtree(site.storage.path(storage_path))


def handle_uploaded_file(site, file, path):
    name = file.name

    storage_path = os.path.join(path, name)
    os_path = os.path.join(site.storage.location, storage_path)
    os_dir, _ = os.path.split(os_path)

    logger.debug("Upload {}".format(os_path))

    os.makedirs(os_dir, exist_ok=True)

    with open(os_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)


def handle_create_directory(site, name, path):
    new_dir = os.path.join(path, name)
    os_path = os.path.join(site.storage.location, new_dir)

    logger.debug("Create directory {}".format(os_path))

    os.makedirs(os_path, exist_ok=True)
