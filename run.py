import argparse
import asyncio
import configparser
from contextlib import closing
import logging
import os

import aiohttp
from aiostream import stream, pipe
from aiovk import API

from core import appstorage
from core.download import Downloader
from core.modules import ModuleCache
from core.session import TokenSession
from core.rate import TokenLimiter
from core.token import get_or_create_token


logger = logging.getLogger(__name__)
logging.getLogger('chardet.charsetprober').setLevel(logging.WARN)


parser = argparse.ArgumentParser(prog='vk-dump')
parser.add_argument('-v', '--verbose', action='store_true')
parser.add_argument('-c', '--config', default='config.txt')
parser.add_argument('-p', '--parallel', type=int, default=8)
parser.add_argument('--app', dest='app_id')

parser.add_argument('login')
parser.add_argument('password')

parser.add_argument('--root', default='./dump/')
parser.add_argument('modules', nargs='+')


def get_app_id(args):
    if args.app_id:
        logger.debug('Using APP_ID from ARGV')
        return args.app_id

    env_id = os.environ.get('VK_APP_ID', None)
    if env_id:
        logger.debug('Using APP_ID from ENV')
        return env_id

    logger.debug('Loading settings from %s', args.config)

    if not os.path.exists(args.config):
        logger.warning('No config file %s exists', args.config)
        return None

    config = configparser.ConfigParser()
    config.read(args.config)

    if 'secrets' not in config:
        logger.warning('No "secrets" section found in config')
        return None
    if 'APP_ID' not in config['secrets']:
        logger.warning('No APP_ID found in config')
        return None

    return config['secrets']['APP_ID']


async def main(args):
    app_id = get_app_id(args)
    if app_id is None:
        logger.critical('No APP_ID found')
        return False

    # Loading modules
    logger.info('Loading modules')
    modules = ModuleCache(args.modules)
    assert modules, 'No modules loaded'

    # Loading token
    with closing(appstorage.create('vk-dump', 'the-island.ru')) as db:
        token = await get_or_create_token(args, app_id, db, modules.scope)

    async with TokenSession(token) as session:
        api = API(session)

        rate = TokenLimiter(args.parallel)
        async with aiohttp.ClientSession() as session:
            if not os.path.isdir(args.root):
                logger.info('Creating root dump directory %s', args.root)
                os.makedirs(args.root)

            downloader = Downloader(args.root, session, rate)

            xs = (
                stream.merge(*[m.get_items(api, rate) for m in modules])
                | pipe.map(downloader.download)  # pylint: disable=E1101
            )

            await xs

    logger.info('Done')


if __name__ == '__main__':
    _args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s %(levelname)8s %(name)s %(message)s',
        level=logging.DEBUG if _args.verbose else logging.INFO,
    )

    main_loop = asyncio.get_event_loop()

    main_loop.run_until_complete(main(_args))
    main_loop.close()
