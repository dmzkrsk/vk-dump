import os
import logging
import shelve

from appdirs import user_data_dir


logger = logging.getLogger()


def create(app_name, author):
    root = user_data_dir(app_name, author)
    path = os.path.join(root, 'local_storage')

    dirname = os.path.dirname(path)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

    logger.info('App DB is %s', path)

    return shelve.open(path)
