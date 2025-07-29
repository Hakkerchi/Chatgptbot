import os
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
from google import generativeai
from dotenv import load_dotenv

# .env fayldan tokenlarni yuklash
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

# Gemini modelini sozlash
generativeai.configure(api_key=GEMINI_API_KEY)
model = generativeai.GenerativeModel('gemini-pro')

# === SQLite bazasi ===
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

def add_user(user_id: int):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

# === AI javoblari ===
async def ask_ai(user_message: str) -> str:
    try:
        response = model.generate_content(user_message)
        return response.text
    except Exception as e:
        return f"⚠️ AI javob bera olmadi:\n{e}"

# === Komandalar ===
async def start_cmd(message: Message):
    add_user(message.from_user.id)
    await message.answer(
        f"👋 Salom, {message.from_user.first_name}!\n"
        "Men Gemini sun’iy intellekti asosidagi botman.\n"
        "Savolingizni yozing!"
    )

async def id_cmd(message: Message):
    await message.answer(f"🆔 Sizning Telegram ID'ingiz: `{message.from_user.id}`", parse_mode="Markdown")

async def users_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ Bu buyruq faqat admin uchun!")
    users = get_all_users()
    await message.answer(f"👥 Foydalanuvchilar soni: {len(users)} ta")

async def sendall_cmd(message: Message, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ Bu buyruq faqat admin uchun!")

    if len(message.text.split()) < 2:
        return await message.answer("❗️ Xabar yozing: /sendall [matn]")

    text = message.text.split(maxsplit=1)[1]
    users = get_all_users()
    sent = 0

    for user_id in users:
        try:
            await bot.send_message(chat_id=user_id, text=text)
            sent += 1
        except:
            continue

    await message.answer(f"✅ {sent} ta foydalanuvchiga yuborildi.")

# === Matnli javoblar ===
async def handle_message(message: Message, bot: Bot):
    add_user(message.from_user.id)
    await message.answer("⏳ AI javob yozmoqda...")
    reply = await ask_ai(message.text)
    await message.answer(reply, parse_mode=ParseMode.HTML)

# === Botni ishga tushurish ===
async def main():
    init_db()
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    dp.message.register(start_cmd, Command("start"))
    dp.message.register(id_cmd, Command("id"))
    dp.message.register(users_cmd, Command("users"))
    dp.message.register(sendall_cmd, Command("sendall"))
    dp.message.register(handle_message, F.text & ~F.via_bot)

    print("✅ Bot ishga tushdi.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())