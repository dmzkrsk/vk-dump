from dataclasses import dataclass
import logging
import os
from stat import ST_MTIME
import time
from typing import Optional


import aiofiles


logger = logging.getLogger(__name__)


CHUNK_SIZE = 50000


@dataclass
class DownloadTask:
    url: str
    ts: Optional[int] = None
    path: Optional[str] = None
    filename: Optional[str] = None


def set_time(path, mtime):
    if mtime is not None:
        st = os.stat(path)
        file_mtime = st[ST_MTIME]

        if int(file_mtime) == int(mtime):
            return
    else:
        mtime = time.time()

    os.utime(path, times=(time.time(), mtime))


class Downloader:
    def __init__(self, root, session, rate):
        self.root = root
        self.session = session
        self.rate = rate

    async def download(self, task: DownloadTask):
        filename = task.filename or task.url.name
        fullpath = os.path.join(self.root, task.path, filename)

        dirname = os.path.dirname(fullpath)
        if not os.path.isdir(dirname):
            logger.debug('[%s] Creating path %r', task.url, dirname)
            os.makedirs(dirname)

        await self.rate.consume()
        async with self.session.get(task.url) as response:
            if not response.status == 200:
                logger.error("Can't load file %s [%d]", task.url, response.status)
                return

            if os.path.exists(fullpath):
                remote_size = response.headers.get('Content-Length')
                if remote_size is not None:
                    remote_size = int(remote_size)
                    file_size = os.path.getsize(fullpath)

                    if file_size == remote_size:
                        set_time(fullpath, task.ts)
                        logger.debug('[%s] Already exists %s', task.url, fullpath)
                        return

                    logger.info('[%s] Incomplete file %s (%d <> %d)', task.url, fullpath, file_size, remote_size)
                else:
                    logger.info('[%s] Unknown remote size, redownloading', task.url)

                os.unlink(fullpath)

            logger.info('[%s] Downloading', task.url)

            async with aiofiles.open(fullpath, 'wb') as out:
                async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                    await out.write(chunk)

            set_time(fullpath, task.ts)
            logger.info('[%s] Finished %s', task.url, fullpath)
