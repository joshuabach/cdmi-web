import os
import logging


logger = logging.getLogger(__name__)


def handle_delete_object(site, name, path, access_token):
    storage_path = os.path.join(path, name)

    logger.debug("Delete {}".format(storage_path))

    site.storage.ensure_connected(access_token)
    site.storage.delete(storage_path)


def handle_uploaded_file(site, file, path, access_token):
    name = file.name

    storage_path = os.path.join(path, name)
    logger.debug("Upload {} to {}".format(storage_path, site))

    site.storage.ensure_connected(access_token)
    site.storage.save(storage_path, file)


def handle_create_directory(site, name, path, access_token):
    new_dir = os.path.join(path, name)

    logger.debug("Create directory {} on {}".format(new_dir, site))

    site.storage.ensure_connected(access_token)
    site.storage.mkdir(new_dir)
