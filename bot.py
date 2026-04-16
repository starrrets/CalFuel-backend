import asyncio
import os
import re
from datetime import date
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import F
from dotenv import load_dotenv

from app.database import SessionLocal, User, Log
from app.main import calculate_daily_norm

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MINI_APP_URL = os.getenv("MINI_APP_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class ProfileStates(StatesGroup):
    gender = State()
    age = State()
    height = State()
    weight = State()
    activity = State()
    goal_type = State()
    goal_percent = State()

# ====================== КЛАВИАТУРА ======================
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="📊 Сегодня")],
            [KeyboardButton(text="📅 История"), KeyboardButton(text="🌍 Язык")]
        ],
        resize_keyboard=True,
        persistent=True
    )

# ====================== КНОПКА ПРОФИЛЬ (умная) ======================
@dp.message(F.text == "👤 Профиль")
async def profile_button(message: Message, state: FSMContext):
    with SessionLocal() as db:
        user = db.query(User).filter(User.tg_id == message.from_user.id).first()
        if user:
            await message.answer(
                f"👤 Текущий профиль:\n"
                f"Пол: {user.gender}\n"
                f"Возраст: {user.age}\n"
                f"Рост: {user.height} см\n"
                f"Вес: {user.weight} кг\n"
                f"Активность: {user.activity}\n"
                f"Цель: {user.goal_type} ({user.goal_percent}%)\n"
                f"Норма: {int(user.daily_norm)} ккал",
                reply_markup=get_main_keyboard()
            )
            return

    # Если профиля нет — начинаем заполнение
    await state.set_state(ProfileStates.gender)
    await message.answer("👤 Твой пол? (male / female)", reply_markup=get_main_keyboard())

# ====================== FSM ЗАПОЛНЕНИЕ ПРОФИЛЯ ======================
@dp.message(ProfileStates.gender)
async def process_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text.lower())
    await state.set_state(ProfileStates.age)
    await message.answer("📅 Сколько тебе лет?")

@dp.message(ProfileStates.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await state.set_state(ProfileStates.height)
    await message.answer("📏 Рост в см?")

@dp.message(ProfileStates.height)
async def process_height(message: Message, state: FSMContext):
    await state.update_data(height=float(message.text))
    await state.set_state(ProfileStates.weight)
    await message.answer("⚖️ Вес в кг?")

@dp.message(ProfileStates.weight)
async def process_weight(message: Message, state: FSMContext):
    await state.update_data(weight=float(message.text))
    await state.set_state(ProfileStates.activity)
    await message.answer("🏃 Уровень активности?\n1.2 — сидячий\n1.375 — лёгкий\n1.55 — умеренный\n1.725 — высокий\n1.9 — очень высокий")

@dp.message(ProfileStates.activity)
async def process_activity(message: Message, state: FSMContext):
    await state.update_data(activity=float(message.text))
    await state.set_state(ProfileStates.goal_type)
    await message.answer("🎯 Цель?\nmaintain — поддержание\ndeficit — дефицит\nsurplus — профицит")

@dp.message(ProfileStates.goal_type)
async def process_goal_type(message: Message, state: FSMContext):
    goal_type = message.text.lower()
    await state.update_data(goal_type=goal_type)
    if goal_type != "maintain":
        await state.set_state(ProfileStates.goal_percent)
        await message.answer("📉 На сколько процентов? (например 10)")
    else:
        await save_profile(message, state)

@dp.message(ProfileStates.goal_percent)
async def process_goal_percent(message: Message, state: FSMContext):
    await state.update_data(goal_percent=float(message.text))
    await save_profile(message, state)

async def save_profile(message: Message, state: FSMContext):
    data = await state.get_data()
    with SessionLocal() as db:
        user = db.query(User).filter(User.tg_id == message.from_user.id).first()
        if not user:
            user = User(tg_id=message.from_user.id)
            db.add(user)

        user.gender = data["gender"]
        user.age = data["age"]
        user.height = data["height"]
        user.weight = data["weight"]
        user.activity = data["activity"]
        user.goal_type = data["goal_type"]
        user.goal_percent = data.get("goal_percent", 0)
        user.units = "metric"

        user.daily_norm = calculate_daily_norm(
            user.gender, user.age, user.height, user.weight,
            user.activity, user.goal_type, user.goal_percent
        )

        db.commit()
        db.refresh(user)

    await message.answer(
        f"✅ Профиль сохранён!\nНорма на сегодня: {int(user.daily_norm)} ккал",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

# ====================== КОМАНДЫ ======================
@dp.message(F.text == "📊 Сегодня")
async def today_button(message: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.tg_id == message.from_user.id).first()
        if not user:
            await message.answer("Сначала настрой профиль 👤 Профиль", reply_markup=get_main_keyboard())
            return
        logs = db.query(Log).filter(Log.tg_id == message.from_user.id, Log.date == date.today()).all()
        total = sum(l.calories for l in logs)
        remaining = int(user.daily_norm - total)

    await message.answer(
        f"📊 Сегодня:\nСъедено: {total} ккал\nОсталось: {remaining} ккал\nНорма: {int(user.daily_norm)} ккал",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "📅 История")
async def history_button(message: Message):
    with SessionLocal() as db:
        logs = db.query(Log).filter(Log.tg_id == message.from_user.id).all()
        result = {}
        for log in logs:
            d = log.date.isoformat()
            result[d] = result.get(d, 0) + log.calories

    if not result:
        await message.answer("Истории пока нет", reply_markup=get_main_keyboard())
        return

    text = "📅 История по дням:\n"
    for d, kcal in sorted(result.items(), reverse=True):
        text += f"{d}: {int(kcal)} ккал\n"
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.message(F.text == "🌍 Язык")
async def lang_button(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang_uk")],
        [InlineKeyboardButton(text="🇪🇸 Español", callback_data="lang_es")],
        [InlineKeyboardButton(text="🇩🇪 Deutsch", callback_data="lang_de")],
        [InlineKeyboardButton(text="🇫🇷 Français", callback_data="lang_fr")],
        [InlineKeyboardButton(text="🇧🇾 Беларуская", callback_data="lang_be")]
    ])
    await message.answer("🌍 Выбери язык бота:", reply_markup=keyboard)

# ====================== ОБРАБОТКА ЕДЫ (самый последний хендлер) ======================
@dp.message(F.text & ~F.text.startswith('/'))
async def handle_food(message: Message, state: FSMContext):
    # Защита от FSM
    if await state.get_state() is not None:
        return

    text = message.text.lower().strip()
    numbers = re.findall(r'\d+', text)
    if not numbers:
        await message.answer("Напиши количество калорий, например «я съел 450» или просто «500»")
        return

    calories = int(numbers[0])
    if calories < 0:
        await message.answer("❌ Отрицательные калории нельзя добавить")
        return

    with SessionLocal() as db:
        log = Log(
            tg_id=message.from_user.id,
            food_name=text[:100],
            calories=calories,
            date=date.today()
        )
        db.add(log)
        db.commit()

        user = db.query(User).filter(User.tg_id == message.from_user.id).first()
        today_logs = db.query(Log).filter(Log.tg_id == message.from_user.id, Log.date == date.today()).all()
        total_today = sum(l.calories for l in today_logs)
        norm = user.daily_norm if user else 2000
        remaining = int(norm - total_today)

    await message.answer(
        f"✅ Добавлено {calories} ккал\n"
        f"Сегодня съедено: {total_today} ккал\n"
        f"Осталось: {remaining} ккал",
        reply_markup=get_main_keyboard()
    )

# ====================== ЗАПУСК ======================
async def main():
    print("🤖 Бот запущен с умной кнопкой Профиль")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())