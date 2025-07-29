import os
import logging
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from google import generativeai
from dotenv import load_dotenv

# .env dagi tokenlarni yuklash
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

# Gemini sozlamasi
generativeai.configure(api_key=GEMINI_API_KEY)
model = generativeai.GenerativeModel("gemini-pro")

# Log sozlamalari
logging.basicConfig(level=logging.INFO)

# Bot va dispatcher
bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

# === SQLite funksiyalar ===
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

# === AI javob funksiyasi ===
def ask_ai(prompt: str) -> str:
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI javob bera olmadi:\n{e}"

# === /start komandasi ===
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    add_user(message.from_user.id)
    await message.answer(f"👋 Salom, {message.from_user.first_name}!\nSavolingizni yozing – Gemini AI javob beradi.")

# === /id komandasi ===
@dp.message_handler(commands=['id'])
async def id_cmd(message: types.Message):
    await message.answer(f"🆔 Sizning Telegram ID'ingiz: <code>{message.from_user.id}</code>")

# === /users komandasi (faqat admin) ===
@dp.message_handler(commands=['users'])
async def users_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Bu buyruq faqat admin uchun!")
    users = get_all_users()
    await message.answer(f"👥 Foydalanuvchilar soni: {len(users)} ta")

# === /sendall komandasi (admin xabari) ===
@dp.message_handler(commands=['sendall'])
async def sendall_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Bu buyruq faqat admin uchun!")

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("❗ Xabar yozing: /sendall [matn]")

    text = parts[1]
    users = get_all_users()
    sent = 0

    for user_id in users:
        try:
            await bot.send_message(chat_id=user_id, text=text)
            sent += 1
        except:
            continue

    await message.reply(f"✅ {sent} ta foydalanuvchiga yuborildi.")

# === Matnli javoblar (AI) ===
@dp.message_handler(lambda message: message.text and not message.text.startswith('/'))
async def ai_handler(message: types.Message):
    add_user(message.from_user.id)
    await message.answer("⏳ AI javob yozmoqda...")
    response = ask_ai(message.text)
    await message.answer(response)

# === Botni ishga tushurish ===
if __name__ == '__main__':
    init_db()
    executor.start_polling(dp, skip_updates=True)