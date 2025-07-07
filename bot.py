from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
import os

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start(message: Message):
    await message.answer("Привет! Я помогу тебе отслеживать закупки 💼")

def run_bot():
    executor.start_polling(dp)