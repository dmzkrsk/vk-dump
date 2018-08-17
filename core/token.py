import logging

from core.session import ImplicitSession


logger = logging.getLogger()


async def _create_token(args, app_id, db, key, scope):
    async with ImplicitSession(args.login, args.password, app_id=app_id, scope=scope) as session:
        logger.info('Authorizing')
        await session.authorize()
        assert session.access_token

        logger.debug('Saving token')
        db[key] = session.access_token

        return session.access_token


async def get_or_create_token(args, app_id, db, scope):
    key = f'tokens.{app_id}.{scope}'
    token = db.get(key, None)

    if token is None:
        logger.debug('No token found')
        return await _create_token(args, app_id, db, key, scope)

    if not isinstance(token, str):
        logger.debug('Invalid token format')
        return await _create_token(args, app_id, db, key, scope)

    logger.debug('Existing token found')
    return token
