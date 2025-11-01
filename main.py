import asyncio
from logger import log_system
from aiogram import Dispatcher, Bot
from config import TOKEN
from handlers import router
import database

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    database.init_db()
    await dp.start_polling(bot)
 
if __name__ == '__main__':
    log_system("Bot is starting up...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_system("Dastur to'xtadi!")
