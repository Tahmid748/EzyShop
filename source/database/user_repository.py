import asyncio
import logging

from psycopg import connect

from source.config.config import DATABASE_URL

logger = logging.getLogger(__name__)


def _is_user_registered(telegram_user_id: int) -> bool:
    """Run the blocking PostgreSQL lookup outside the Telegram event loop."""
    with connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS("
                "SELECT 1 FROM registered_users WHERE telegram_user_id = %s"
                ")",
                (telegram_user_id,),
            )
            row = cursor.fetchone()
            return bool(row and row[0])


async def is_user_registered(telegram_user_id: int) -> bool:
    """Return whether a Telegram user has an entry in ``registered_users``.

    Psycopg's async mode is incompatible with Windows' default
    ``ProactorEventLoop``.  A synchronous query is run in a worker thread so
    the bot's event loop remains unblocked while retaining Windows support.
    """
    if not DATABASE_URL:
        logger.warning("DATABASE_URL is not configured; treating user as unregistered")
        return False

    try:
        return await asyncio.to_thread(_is_user_registered, telegram_user_id)
    except Exception:
        # Do not prevent users from receiving a response if the database is
        # temporarily unavailable.  In that case we safely omit registered
        # user behaviour from the response generator.
        logger.exception("Could not check registration for Telegram user %s", telegram_user_id)
        return False
