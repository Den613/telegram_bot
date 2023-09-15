
import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from devtools import debug
from time_select import *
from models import *
from start import *



TOKEN = '***'

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)

    dp = Dispatcher()

    sub_router.include_router(deep_dark_router)
    router.include_routers(sub_router, sub_sub_router)
    dp.include_router(router)

    # Start event dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())