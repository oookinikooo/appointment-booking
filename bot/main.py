import asyncio
import logging
from datetime import datetime

import aiocron
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from src.config import config
from src.handlers import attach_handlers
from src.services.booking import Booking
from src.utils.tools import startup

logging.basicConfig(level="INFO",
                    format="%(asctime)s [%(levelname)s]: %(name)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

logger = logging.getLogger(__name__)

async def main():
    await Booking.init_db()

    bot = Bot(token=config.token,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    @aiocron.crontab("5 0 * * *")
    async def job_1_remove_expired_sessions():
        now = datetime.now()
        sessions = await Booking.get_expired_sessions()
        expired = []
        for s in sessions:
            if s.time.hour == 0 and s.date.month >= now.month:
                continue
            if s.date == now.date() and s.time > now.time():
                continue
            expired.append(s)

        if expired:
            log_msg = f"Found {len(expired)} expired sessions:\n"
            for s in expired:
                is_ok = await Booking.delete(s.id)
                log_msg += f"\n * Del {s.date:%d.%m.%y} at {s.time:%H:%M:%S} " \
                           f"{'success' if is_ok else 'failed'}"
            logger.info(log_msg)

    dp = Dispatcher()
    dp.startup.register(startup)

    attach_handlers(dp)

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    except Exception:
        logger.exception("pooling down")
    else:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
