import logging
import pprint

from yarl import URL

from core.download import DownloadTask


SCOPE = 2 | 4  # https://vk.com/dev/permissions
logger = logging.getLogger(__name__)


def _locate_image(photo):  # pylint: disable=R1710
    w = photo.get('width')
    h = photo.get('height')

    if w is None and h is None:
        sizes = {
            s['type']: s['url']
            for s in photo['sizes']
        }

        for size in 'wzyxms':
            if size not in sizes:
                continue

            return URL(sizes[size])

        assert False, pprint.pprint(sizes)

    for photo_size in photo['sizes']:
        if w == photo_size['width'] and h == photo_size['height']:
            return URL(photo_size['url'])

    assert False, pprint.pprint(sizes)


def _download_all(path, photos):
    for photo in photos:
        yield DownloadTask(
            url=_locate_image(photo),
            ts=photo['date'],
            path=path,
        )


async def get_items(api, rate):
    await rate.consume()
    albums = await api('photos.getAlbums')

    logger.debug('%d albums found', albums['count'])

    for album in albums['items']:
        album_name = album['title']
        logger.info('Found album %r', album_name)

        await rate.consume()
        photos = await api('photos.get', photo_sizes=1, album_id=album['id'])
        logger.info('Downloading %d images from album %r', photos['count'], album_name)

        for item in _download_all(f'albums/{album_name}/', photos['items']):
            yield item

        # TODO catch finish

    # Избранные фотки
    offset = 0
    total_size = 0

    while True:
        await rate.consume()
        logger.debug('Downloading pictures from favourites offset %d of %d', offset, total_size)
        photos = await api('fave.getPhotos', photo_sizes=1, count=100, offset=offset)

        assert not total_size or total_size == photos['count']

        total_size = photos['count']
        page_size = len(photos['items'])

        logger.info('Downloading %d pictures from favourites', offset + page_size)

        for item in _download_all('favs/images', photos['items']):
            yield item

        offset += page_size

        assert offset <= photos['count']
        if offset == photos['count']:
            break
