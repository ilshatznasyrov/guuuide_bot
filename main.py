import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.markdown import hbold
from aiogram.filters import CommandStart
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta
import db  # модуль работы с SQLite
from messages import AUTOFLOW_MESSAGES  # цепочка сообщений

# Загружаем переменные из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PDF_LINK = os.getenv("PDF_LINK")
PRESENT_LINK = os.getenv("PRESENT_LINK")


if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())


# Кнопка для подписки и получения PDF
def get_main_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подписался на канал", callback_data="check_sub")],
    ])
    return kb


# FSM состояние для запроса email
class Form(StatesGroup):
    waiting_for_email = State()


# /start
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    text = (
        f"{hbold('Привет!')}\n\n"
        "📘 Получи гайд «3 фразы, которые снимают 80% вопросов от клиентов».\n\n"
        f"Чтобы получить PDF:\n1. Подпишись на канал {CHANNEL_ID}\n2. Нажми кнопку ниже 👇"
    )
    await message.answer(text, reply_markup=get_main_kb())


# Проверка подписки, выдача PDF и запуск сбора email
@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    from_user = callback.from_user

    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status not in ("left", "kicked"):
            # Проверяем, есть ли пользователь в базе
            if not db.user_exists(user_id):
                db.add_user(
                    user_id=user_id,
                    full_name=from_user.full_name,
                    username=from_user.username
                )

            await callback.message.answer(
                f"🎁 Вот твой гайд:\n👉 <a href='{PDF_LINK}'>Скачать PDF</a>",
                disable_web_page_preview=True
            )

            # Запрашиваем email, если он не сохранён
            email = db.get_user_email(user_id)
            if not email:
                await callback.message.answer("Пожалуйста, введи свой email, чтобы получать полезные рассылки:")
                await state.set_state(Form.waiting_for_email)
            else:
                await callback.message.answer("Мы уже получили твой email. Спасибо!")

        else:
            await callback.message.answer("Пожалуйста, подпишись на канал и нажми кнопку ещё раз.")
    except Exception as e:
        await callback.message.answer("Не удалось проверить подписку. Попробуй позже.")


# Обработка email
@dp.message(Form.waiting_for_email)
async def email_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    email = message.text.strip()

    # Простая проверка email
    if '@' not in email or '.' not in email:
        await message.answer("Пожалуйста, введи корректный email.")
        return

    db.set_email(user_id, email)
    await message.answer("Спасибо! Твой email сохранён. Теперь ты будешь получать полезные сообщения.")
    await state.clear()


@dp.message(F.text.lower() == "хочу подарок")
async def handle_gift_request(message: types.Message):
    await message.answer(
        "🎁 Держи наш авторский шаблон для ответов на «А почему так дорого?»\n\n"
        f"👉 <a href='{PRESENT_LINK}'>Скачать PDF</a>",
        disable_web_page_preview=True
    )


# Функция автоворонки — запускается в фоне
async def send_scheduled_messages():
    while True:
        users = db.get_all_users()
        now = datetime.now()

        for user_id, start_date_str, email in users:
            start_date = datetime.fromisoformat(start_date_str)
            day_num = (now.date() - start_date.date()).days
            if 0 <= day_num < len(AUTOFLOW_MESSAGES):
                try:
                    await bot.send_message(user_id, AUTOFLOW_MESSAGES[day_num])
                except Exception as e:
                    print(f"Ошибка при отправке сообщения {user_id}: {e}")

        await asyncio.sleep(24 * 3600)  # один раз в сутки

if __name__ == "__main__":
    import db
    db.init_db()

    async def main():
        asyncio.create_task(send_scheduled_messages())
        await dp.start_polling(bot)

    asyncio.run(main())
