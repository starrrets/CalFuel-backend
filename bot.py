import asyncio
import os
import re
from datetime import date
from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import F
from dotenv import load_dotenv

from app.database import SessionLocal, User, Log, Base, engine

Base.metadata.create_all(bind=engine)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MINI_APP_URL = os.getenv("MINI_APP_URL", "")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ====================== TRANSLATIONS ======================

STRINGS = {
    "ru": {
        "btn_main_profile": "👤 Профиль",
        "btn_main_today": "📊 Сегодня",
        "btn_main_history": "📅 История",
        "btn_main_lang": "🌍 Язык",
        "btn_main_app": "🍊 Открыть приложение",
        "start": (
            "👋 Привет! Я трекер калорий.\n\n"
            "Нажми «👤 Профиль», чтобы указать свои данные и получить персональную норму калорий.\n"
            "После этого просто пиши мне, что съел, — я всё посчитаю."
        ),
        "profile_view": (
            "👤 Твой профиль:\n\n"
            "Пол: {gender}\n"
            "Возраст: {age} лет\n"
            "Рост: {height} см\n"
            "Вес: {weight} кг\n"
            "Активность: {activity_label}\n"
            "Цель: {goal_label}\n"
            "Норма: {daily_norm} ккал/день\n\n"
            "Чтобы изменить данные, нажми /reset"
        ),
        "ask_gender": "👤 Укажи свой пол:",
        "btn_male": "👨 Мужской",
        "btn_female": "👩 Женский",
        "err_gender": "Пожалуйста, выбери пол из кнопок ниже.",
        "ask_age": "📅 Сколько тебе лет?",
        "err_age": "Введи корректный возраст — целое число от 10 до 120.",
        "ask_height": "📏 Рост в сантиметрах? (например: 175)",
        "err_height": "Введи рост в сантиметрах — число от 100 до 250.",
        "ask_weight": "⚖️ Вес в килограммах? (например: 70)",
        "err_weight": "Введи вес в килограммах — число от 30 до 300.",
        "ask_activity": (
            "🏃 Выбери уровень физической активности:\n\n"
            "🪑 Сидячий — офис, почти нет нагрузок\n"
            "🚶 Лёгкий — прогулки, 1–3 тренировки в неделю\n"
            "🏋️ Умеренный — 3–5 тренировок в неделю\n"
            "🔥 Высокий — 6–7 тренировок в неделю\n"
            "⚡ Очень высокий — физический труд или 2 тренировки в день"
        ),
        "btn_activity_sedentary": "🪑 Сидячий",
        "btn_activity_light": "🚶 Лёгкий",
        "btn_activity_moderate": "🏋️ Умеренный",
        "btn_activity_high": "🔥 Высокий",
        "btn_activity_very_high": "⚡ Очень высокий",
        "err_activity": "Пожалуйста, выбери уровень активности из кнопок.",
        "ask_goal": "🎯 Какая у тебя цель?",
        "btn_goal_maintain": "⚖️ Поддержание веса",
        "btn_goal_deficit": "📉 Похудение (дефицит)",
        "btn_goal_surplus": "📈 Набор массы (профицит)",
        "err_goal": "Пожалуйста, выбери цель из кнопок.",
        "ask_goal_percent": (
            "📉 На сколько процентов изменить калорийность?\n\n"
            "Рекомендуется: 10–20% для мягкого эффекта, до 30% — для активного."
        ),
        "err_goal_percent": "Введи число от 1 до 50 (например: 15).",
        "profile_saved": "✅ Профиль сохранён! Твоя норма: {daily_norm} ккал/день.",
        "today_no_profile": "Сначала настрой профиль — нажми «👤 Профиль».",
        "today": (
            "📊 Сегодня:\n\n"
            "Съедено: {eaten} ккал\n"
            "Осталось: {remaining} ккал\n"
            "Норма: {norm} ккал"
        ),
        "history_empty": "Записей пока нет. Начни отслеживать питание!",
        "history_header": "📅 История питания:\n\n",
        "history_row": "{date}: {kcal} ккал\n",
        "lang_choose": "🌍 Выбери язык:",
        "lang_changed": "✅ Язык изменён на {lang_name}.",
        "food_hint": "Напиши, что съел и сколько калорий, например:\n«гречка 350» или просто «500»",
        "food_added": "✅ +{calories} ккал\nСегодня: {eaten} ккал  |  Осталось: {remaining} ккал",
        "err_zero_cal": "❌ Калорий должно быть больше нуля.",
        "gender_male": "Мужской",
        "gender_female": "Женский",
        "goal_maintain": "Поддержание веса",
        "goal_deficit": "Похудение −{pct}%",
        "goal_surplus": "Набор массы +{pct}%",
        "activity_sedentary": "Сидячий (1.2)",
        "activity_light": "Лёгкий (1.375)",
        "activity_moderate": "Умеренный (1.55)",
        "activity_high": "Высокий (1.725)",
        "activity_very_high": "Очень высокий (1.9)",
    },
    "en": {
        "btn_main_profile": "👤 Profile",
        "btn_main_today": "📊 Today",
        "btn_main_history": "📅 History",
        "btn_main_lang": "🌍 Language",
        "btn_main_app": "🍊 Open app",
        "start": (
            "👋 Hi! I'm a calorie tracker.\n\n"
            "Tap «👤 Profile» to enter your details and get your personal calorie goal.\n"
            "Then just tell me what you ate and I'll log it for you."
        ),
        "profile_view": (
            "👤 Your profile:\n\n"
            "Gender: {gender}\n"
            "Age: {age}\n"
            "Height: {height} cm\n"
            "Weight: {weight} kg\n"
            "Activity: {activity_label}\n"
            "Goal: {goal_label}\n"
            "Daily norm: {daily_norm} kcal/day\n\n"
            "To update your data, send /reset"
        ),
        "ask_gender": "👤 What is your gender?",
        "btn_male": "👨 Male",
        "btn_female": "👩 Female",
        "err_gender": "Please choose your gender using the buttons below.",
        "ask_age": "📅 How old are you?",
        "err_age": "Please enter a valid age — a whole number between 10 and 120.",
        "ask_height": "📏 Your height in centimetres? (e.g. 175)",
        "err_height": "Please enter your height in centimetres — a number between 100 and 250.",
        "ask_weight": "⚖️ Your weight in kilograms? (e.g. 70)",
        "err_weight": "Please enter your weight in kilograms — a number between 30 and 300.",
        "ask_activity": (
            "🏃 Choose your physical activity level:\n\n"
            "🪑 Sedentary — desk job, little or no exercise\n"
            "🚶 Light — light exercise 1–3 days/week\n"
            "🏋️ Moderate — exercise 3–5 days/week\n"
            "🔥 High — hard exercise 6–7 days/week\n"
            "⚡ Very high — physical job or twice-a-day training"
        ),
        "btn_activity_sedentary": "🪑 Sedentary",
        "btn_activity_light": "🚶 Light",
        "btn_activity_moderate": "🏋️ Moderate",
        "btn_activity_high": "🔥 High",
        "btn_activity_very_high": "⚡ Very high",
        "err_activity": "Please choose your activity level using the buttons.",
        "ask_goal": "🎯 What is your goal?",
        "btn_goal_maintain": "⚖️ Maintain weight",
        "btn_goal_deficit": "📉 Lose weight (deficit)",
        "btn_goal_surplus": "📈 Gain weight (surplus)",
        "err_goal": "Please choose a goal using the buttons.",
        "ask_goal_percent": (
            "📉 By how many percent should I adjust your calories?\n\n"
            "Recommended: 10–20% for a gentle effect, up to 30% for an active approach."
        ),
        "err_goal_percent": "Please enter a number between 1 and 50 (e.g. 15).",
        "profile_saved": "✅ Profile saved! Your daily norm: {daily_norm} kcal/day.",
        "today_no_profile": "Set up your profile first — tap «👤 Profile».",
        "today": (
            "📊 Today:\n\n"
            "Eaten: {eaten} kcal\n"
            "Remaining: {remaining} kcal\n"
            "Norm: {norm} kcal"
        ),
        "history_empty": "No records yet. Start tracking your meals!",
        "history_header": "📅 Calorie history:\n\n",
        "history_row": "{date}: {kcal} kcal\n",
        "lang_choose": "🌍 Choose a language:",
        "lang_changed": "✅ Language changed to {lang_name}.",
        "food_hint": "Tell me what you ate and the calories, for example:\n«oatmeal 350» or just «500»",
        "food_added": "✅ +{calories} kcal\nToday: {eaten} kcal  |  Remaining: {remaining} kcal",
        "err_zero_cal": "❌ Calories must be greater than zero.",
        "gender_male": "Male",
        "gender_female": "Female",
        "goal_maintain": "Maintain weight",
        "goal_deficit": "Lose weight −{pct}%",
        "goal_surplus": "Gain weight +{pct}%",
        "activity_sedentary": "Sedentary (1.2)",
        "activity_light": "Light (1.375)",
        "activity_moderate": "Moderate (1.55)",
        "activity_high": "High (1.725)",
        "activity_very_high": "Very high (1.9)",
    },
    "uk": {
        "btn_main_profile": "👤 Профіль",
        "btn_main_today": "📊 Сьогодні",
        "btn_main_history": "📅 Історія",
        "btn_main_lang": "🌍 Мова",
        "btn_main_app": "🍊 Відкрити додаток",
        "start": (
            "👋 Привіт! Я трекер калорій.\n\n"
            "Натисни «👤 Профіль», щоб вказати свої дані та отримати персональну норму калорій.\n"
            "Після цього просто пиши мені, що з'їв, — я все порахую."
        ),
        "profile_view": (
            "👤 Твій профіль:\n\n"
            "Стать: {gender}\n"
            "Вік: {age} років\n"
            "Зріст: {height} см\n"
            "Вага: {weight} кг\n"
            "Активність: {activity_label}\n"
            "Ціль: {goal_label}\n"
            "Норма: {daily_norm} ккал/день\n\n"
            "Щоб змінити дані, надішли /reset"
        ),
        "ask_gender": "👤 Вкажи свою стать:",
        "btn_male": "👨 Чоловіча",
        "btn_female": "👩 Жіноча",
        "err_gender": "Будь ласка, обери стать за допомогою кнопок.",
        "ask_age": "📅 Скільки тобі років?",
        "err_age": "Введи коректний вік — ціле число від 10 до 120.",
        "ask_height": "📏 Зріст у сантиметрах? (наприклад: 175)",
        "err_height": "Введи зріст у сантиметрах — число від 100 до 250.",
        "ask_weight": "⚖️ Вага в кілограмах? (наприклад: 70)",
        "err_weight": "Введи вагу в кілограмах — число від 30 до 300.",
        "ask_activity": (
            "🏃 Обери рівень фізичної активності:\n\n"
            "🪑 Сидячий — офіс, майже немає навантажень\n"
            "🚶 Легкий — прогулянки, 1–3 тренування на тиждень\n"
            "🏋️ Помірний — 3–5 тренувань на тиждень\n"
            "🔥 Високий — 6–7 тренувань на тиждень\n"
            "⚡ Дуже високий — фізична праця або 2 тренування на день"
        ),
        "btn_activity_sedentary": "🪑 Сидячий",
        "btn_activity_light": "🚶 Легкий",
        "btn_activity_moderate": "🏋️ Помірний",
        "btn_activity_high": "🔥 Високий",
        "btn_activity_very_high": "⚡ Дуже високий",
        "err_activity": "Будь ласка, обери рівень активності з кнопок.",
        "ask_goal": "🎯 Яка у тебе ціль?",
        "btn_goal_maintain": "⚖️ Підтримання ваги",
        "btn_goal_deficit": "📉 Схуднення (дефіцит)",
        "btn_goal_surplus": "📈 Набір маси (профіцит)",
        "err_goal": "Будь ласка, обери ціль з кнопок.",
        "ask_goal_percent": (
            "📉 На скільки відсотків змінити калорійність?\n\n"
            "Рекомендовано: 10–20% для м'якого ефекту, до 30% — для активного."
        ),
        "err_goal_percent": "Введи число від 1 до 50 (наприклад: 15).",
        "profile_saved": "✅ Профіль збережено! Твоя норма: {daily_norm} ккал/день.",
        "today_no_profile": "Спочатку налаштуй профіль — натисни «👤 Профіль».",
        "today": (
            "📊 Сьогодні:\n\n"
            "З'їдено: {eaten} ккал\n"
            "Залишилось: {remaining} ккал\n"
            "Норма: {norm} ккал"
        ),
        "history_empty": "Записів поки немає. Починай відстежувати харчування!",
        "history_header": "📅 Історія харчування:\n\n",
        "history_row": "{date}: {kcal} ккал\n",
        "lang_choose": "🌍 Обери мову:",
        "lang_changed": "✅ Мову змінено на {lang_name}.",
        "food_hint": "Напиши, що з'їв і скільки калорій, наприклад:\n«гречка 350» або просто «500»",
        "food_added": "✅ +{calories} ккал\nСьогодні: {eaten} ккал  |  Залишилось: {remaining} ккал",
        "err_zero_cal": "❌ Калорій має бути більше нуля.",
        "gender_male": "Чоловіча",
        "gender_female": "Жіноча",
        "goal_maintain": "Підтримання ваги",
        "goal_deficit": "Схуднення −{pct}%",
        "goal_surplus": "Набір маси +{pct}%",
        "activity_sedentary": "Сидячий (1.2)",
        "activity_light": "Легкий (1.375)",
        "activity_moderate": "Помірний (1.55)",
        "activity_high": "Високий (1.725)",
        "activity_very_high": "Дуже високий (1.9)",
    },
    "es": {
        "btn_main_profile": "👤 Perfil",
        "btn_main_today": "📊 Hoy",
        "btn_main_history": "📅 Historial",
        "btn_main_lang": "🌍 Idioma",
        "btn_main_app": "🍊 Abrir app",
        "start": (
            "👋 ¡Hola! Soy un rastreador de calorías.\n\n"
            "Toca «👤 Perfil» para ingresar tus datos y obtener tu objetivo calórico personal.\n"
            "Después solo cuéntame qué comiste y yo lo registraré."
        ),
        "profile_view": (
            "👤 Tu perfil:\n\n"
            "Género: {gender}\n"
            "Edad: {age} años\n"
            "Altura: {height} cm\n"
            "Peso: {weight} kg\n"
            "Actividad: {activity_label}\n"
            "Objetivo: {goal_label}\n"
            "Norma: {daily_norm} kcal/día\n\n"
            "Para actualizar tus datos, envía /reset"
        ),
        "ask_gender": "👤 ¿Cuál es tu género?",
        "btn_male": "👨 Masculino",
        "btn_female": "👩 Femenino",
        "err_gender": "Por favor, elige tu género con los botones.",
        "ask_age": "📅 ¿Cuántos años tienes?",
        "err_age": "Introduce una edad válida — un número entero entre 10 y 120.",
        "ask_height": "📏 ¿Tu altura en centímetros? (ej.: 175)",
        "err_height": "Introduce tu altura en centímetros — un número entre 100 y 250.",
        "ask_weight": "⚖️ ¿Tu peso en kilogramos? (ej.: 70)",
        "err_weight": "Introduce tu peso en kilogramos — un número entre 30 y 300.",
        "ask_activity": (
            "🏃 Elige tu nivel de actividad física:\n\n"
            "🪑 Sedentario — trabajo de escritorio, poco ejercicio\n"
            "🚶 Ligero — ejercicio 1–3 días/semana\n"
            "🏋️ Moderado — ejercicio 3–5 días/semana\n"
            "🔥 Alto — ejercicio intenso 6–7 días/semana\n"
            "⚡ Muy alto — trabajo físico o doble entrenamiento diario"
        ),
        "btn_activity_sedentary": "🪑 Sedentario",
        "btn_activity_light": "🚶 Ligero",
        "btn_activity_moderate": "🏋️ Moderado",
        "btn_activity_high": "🔥 Alto",
        "btn_activity_very_high": "⚡ Muy alto",
        "err_activity": "Por favor, elige el nivel de actividad con los botones.",
        "ask_goal": "🎯 ¿Cuál es tu objetivo?",
        "btn_goal_maintain": "⚖️ Mantener peso",
        "btn_goal_deficit": "📉 Perder peso (déficit)",
        "btn_goal_surplus": "📈 Ganar masa (superávit)",
        "err_goal": "Por favor, elige un objetivo con los botones.",
        "ask_goal_percent": (
            "📉 ¿En qué porcentaje ajusto tus calorías?\n\n"
            "Recomendado: 10–20% para un efecto suave, hasta 30% activo."
        ),
        "err_goal_percent": "Introduce un número entre 1 y 50 (ej.: 15).",
        "profile_saved": "✅ ¡Perfil guardado! Tu norma: {daily_norm} kcal/día.",
        "today_no_profile": "Primero configura tu perfil — toca «👤 Perfil».",
        "today": (
            "📊 Hoy:\n\n"
            "Consumido: {eaten} kcal\n"
            "Restante: {remaining} kcal\n"
            "Norma: {norm} kcal"
        ),
        "history_empty": "Aún no hay registros. ¡Empieza a rastrear tus comidas!",
        "history_header": "📅 Historial de calorías:\n\n",
        "history_row": "{date}: {kcal} kcal\n",
        "lang_choose": "🌍 Elige un idioma:",
        "lang_changed": "✅ Idioma cambiado a {lang_name}.",
        "food_hint": "Cuéntame qué comiste y las calorías, por ejemplo:\n«avena 350» o simplemente «500»",
        "food_added": "✅ +{calories} kcal\nHoy: {eaten} kcal  |  Restante: {remaining} kcal",
        "err_zero_cal": "❌ Las calorías deben ser mayores que cero.",
        "gender_male": "Masculino",
        "gender_female": "Femenino",
        "goal_maintain": "Mantener peso",
        "goal_deficit": "Perder peso −{pct}%",
        "goal_surplus": "Ganar masa +{pct}%",
        "activity_sedentary": "Sedentario (1.2)",
        "activity_light": "Ligero (1.375)",
        "activity_moderate": "Moderado (1.55)",
        "activity_high": "Alto (1.725)",
        "activity_very_high": "Muy alto (1.9)",
    },
    "de": {
        "btn_main_profile": "👤 Profil",
        "btn_main_today": "📊 Heute",
        "btn_main_history": "📅 Verlauf",
        "btn_main_lang": "🌍 Sprache",
        "btn_main_app": "🍊 App öffnen",
        "start": (
            "👋 Hallo! Ich bin ein Kalorien-Tracker.\n\n"
            "Tippe auf «👤 Profil», um deine Daten einzugeben und dein persönliches Kalorienziel zu erhalten.\n"
            "Dann schreib mir einfach, was du gegessen hast — ich tracke es für dich."
        ),
        "profile_view": (
            "👤 Dein Profil:\n\n"
            "Geschlecht: {gender}\n"
            "Alter: {age} Jahre\n"
            "Größe: {height} cm\n"
            "Gewicht: {weight} kg\n"
            "Aktivität: {activity_label}\n"
            "Ziel: {goal_label}\n"
            "Tagesnorm: {daily_norm} kcal/Tag\n\n"
            "Um deine Daten zu ändern, sende /reset"
        ),
        "ask_gender": "👤 Was ist dein Geschlecht?",
        "btn_male": "👨 Männlich",
        "btn_female": "👩 Weiblich",
        "err_gender": "Bitte wähle dein Geschlecht über die Schaltflächen.",
        "ask_age": "📅 Wie alt bist du?",
        "err_age": "Bitte gib ein gültiges Alter ein — eine ganze Zahl zwischen 10 und 120.",
        "ask_height": "📏 Deine Körpergröße in Zentimetern? (z. B. 175)",
        "err_height": "Bitte gib deine Größe in Zentimetern ein — eine Zahl zwischen 100 und 250.",
        "ask_weight": "⚖️ Dein Gewicht in Kilogramm? (z. B. 70)",
        "err_weight": "Bitte gib dein Gewicht in Kilogramm ein — eine Zahl zwischen 30 und 300.",
        "ask_activity": (
            "🏃 Wähle dein körperliches Aktivitätsniveau:\n\n"
            "🪑 Sitzend — Büroarbeit, kaum Bewegung\n"
            "🚶 Leicht — leichte Bewegung 1–3 Tage/Woche\n"
            "🏋️ Moderat — Training 3–5 Tage/Woche\n"
            "🔥 Hoch — intensives Training 6–7 Tage/Woche\n"
            "⚡ Sehr hoch — körperliche Arbeit oder zweimal täglich Training"
        ),
        "btn_activity_sedentary": "🪑 Sitzend",
        "btn_activity_light": "🚶 Leicht",
        "btn_activity_moderate": "🏋️ Moderat",
        "btn_activity_high": "🔥 Hoch",
        "btn_activity_very_high": "⚡ Sehr hoch",
        "err_activity": "Bitte wähle dein Aktivitätsniveau über die Schaltflächen.",
        "ask_goal": "🎯 Was ist dein Ziel?",
        "btn_goal_maintain": "⚖️ Gewicht halten",
        "btn_goal_deficit": "📉 Abnehmen (Defizit)",
        "btn_goal_surplus": "📈 Zunehmen (Überschuss)",
        "err_goal": "Bitte wähle ein Ziel über die Schaltflächen.",
        "ask_goal_percent": (
            "📉 Um wie viel Prozent soll ich deine Kalorien anpassen?\n\n"
            "Empfohlen: 10–20% für einen sanften Effekt, bis 30% für aktives Vorgehen."
        ),
        "err_goal_percent": "Bitte gib eine Zahl zwischen 1 und 50 ein (z. B. 15).",
        "profile_saved": "✅ Profil gespeichert! Deine Tagesnorm: {daily_norm} kcal/Tag.",
        "today_no_profile": "Richte zuerst dein Profil ein — tippe auf «👤 Profil».",
        "today": (
            "📊 Heute:\n\n"
            "Gegessen: {eaten} kcal\n"
            "Übrig: {remaining} kcal\n"
            "Norm: {norm} kcal"
        ),
        "history_empty": "Noch keine Einträge. Fang an, deine Mahlzeiten zu tracken!",
        "history_header": "📅 Kalorienhistorie:\n\n",
        "history_row": "{date}: {kcal} kcal\n",
        "lang_choose": "🌍 Wähle eine Sprache:",
        "lang_changed": "✅ Sprache geändert auf {lang_name}.",
        "food_hint": "Schreib, was du gegessen hast und wie viele Kalorien, z. B.:\n«Haferbrei 350» oder einfach «500»",
        "food_added": "✅ +{calories} kcal\nHeute: {eaten} kcal  |  Übrig: {remaining} kcal",
        "err_zero_cal": "❌ Kalorien müssen größer als null sein.",
        "gender_male": "Männlich",
        "gender_female": "Weiblich",
        "goal_maintain": "Gewicht halten",
        "goal_deficit": "Abnehmen −{pct}%",
        "goal_surplus": "Zunehmen +{pct}%",
        "activity_sedentary": "Sitzend (1.2)",
        "activity_light": "Leicht (1.375)",
        "activity_moderate": "Moderat (1.55)",
        "activity_high": "Hoch (1.725)",
        "activity_very_high": "Sehr hoch (1.9)",
    },
    "fr": {
        "btn_main_profile": "👤 Profil",
        "btn_main_today": "📊 Aujourd'hui",
        "btn_main_history": "📅 Historique",
        "btn_main_lang": "🌍 Langue",
        "btn_main_app": "🍊 Ouvrir l'app",
        "start": (
            "👋 Bonjour ! Je suis un tracker de calories.\n\n"
            "Appuie sur «👤 Profil» pour entrer tes données et obtenir ton objectif calorique personnel.\n"
            "Ensuite, dis-moi simplement ce que tu as mangé — je l'enregistrerai."
        ),
        "profile_view": (
            "👤 Ton profil :\n\n"
            "Genre : {gender}\n"
            "Âge : {age} ans\n"
            "Taille : {height} cm\n"
            "Poids : {weight} kg\n"
            "Activité : {activity_label}\n"
            "Objectif : {goal_label}\n"
            "Norme : {daily_norm} kcal/jour\n\n"
            "Pour mettre à jour tes données, envoie /reset"
        ),
        "ask_gender": "👤 Quel est ton genre ?",
        "btn_male": "👨 Masculin",
        "btn_female": "👩 Féminin",
        "err_gender": "Merci de choisir ton genre via les boutons.",
        "ask_age": "📅 Quel âge as-tu ?",
        "err_age": "Entre un âge valide — un entier entre 10 et 120.",
        "ask_height": "📏 Ta taille en centimètres ? (ex. : 175)",
        "err_height": "Entre ta taille en centimètres — un nombre entre 100 et 250.",
        "ask_weight": "⚖️ Ton poids en kilogrammes ? (ex. : 70)",
        "err_weight": "Entre ton poids en kilogrammes — un nombre entre 30 et 300.",
        "ask_activity": (
            "🏃 Choisis ton niveau d'activité physique :\n\n"
            "🪑 Sédentaire — bureau, peu d'exercice\n"
            "🚶 Léger — exercice 1–3 jours/semaine\n"
            "🏋️ Modéré — exercice 3–5 jours/semaine\n"
            "🔥 Élevé — exercice intense 6–7 jours/semaine\n"
            "⚡ Très élevé — travail physique ou double entraînement quotidien"
        ),
        "btn_activity_sedentary": "🪑 Sédentaire",
        "btn_activity_light": "🚶 Léger",
        "btn_activity_moderate": "🏋️ Modéré",
        "btn_activity_high": "🔥 Élevé",
        "btn_activity_very_high": "⚡ Très élevé",
        "err_activity": "Merci de choisir ton niveau d'activité via les boutons.",
        "ask_goal": "🎯 Quel est ton objectif ?",
        "btn_goal_maintain": "⚖️ Maintenir le poids",
        "btn_goal_deficit": "📉 Perdre du poids (déficit)",
        "btn_goal_surplus": "📈 Prendre de la masse (surplus)",
        "err_goal": "Merci de choisir un objectif via les boutons.",
        "ask_goal_percent": (
            "📉 De quel pourcentage dois-je ajuster tes calories ?\n\n"
            "Recommandé : 10–20 % pour un effet doux, jusqu'à 30 % pour une approche active."
        ),
        "err_goal_percent": "Entre un nombre entre 1 et 50 (ex. : 15).",
        "profile_saved": "✅ Profil enregistré ! Ta norme : {daily_norm} kcal/jour.",
        "today_no_profile": "Configure d'abord ton profil — appuie sur «👤 Profil».",
        "today": (
            "📊 Aujourd'hui :\n\n"
            "Consommé : {eaten} kcal\n"
            "Restant : {remaining} kcal\n"
            "Norme : {norm} kcal"
        ),
        "history_empty": "Pas encore d'enregistrements. Commence à suivre tes repas !",
        "history_header": "📅 Historique calorique :\n\n",
        "history_row": "{date} : {kcal} kcal\n",
        "lang_choose": "🌍 Choisis une langue :",
        "lang_changed": "✅ Langue changée en {lang_name}.",
        "food_hint": "Dis-moi ce que tu as mangé et les calories, par exemple :\n«flocons d'avoine 350» ou simplement «500»",
        "food_added": "✅ +{calories} kcal\nAujourd'hui : {eaten} kcal  |  Restant : {remaining} kcal",
        "err_zero_cal": "❌ Les calories doivent être supérieures à zéro.",
        "gender_male": "Masculin",
        "gender_female": "Féminin",
        "goal_maintain": "Maintenir le poids",
        "goal_deficit": "Perdre du poids −{pct}%",
        "goal_surplus": "Prendre de la masse +{pct}%",
        "activity_sedentary": "Sédentaire (1.2)",
        "activity_light": "Léger (1.375)",
        "activity_moderate": "Modéré (1.55)",
        "activity_high": "Élevé (1.725)",
        "activity_very_high": "Très élevé (1.9)",
    },
    "be": {
        "btn_main_profile": "👤 Профіль",
        "btn_main_today": "📊 Сёння",
        "btn_main_history": "📅 Гісторыя",
        "btn_main_lang": "🌍 Мова",
        "btn_main_app": "🍊 Адкрыць праграму",
        "start": (
            "👋 Прывітанне! Я трэкер калорый.\n\n"
            "Націсні «👤 Профіль», каб указаць свае дадзеныя і атрымаць персанальную норму калорый.\n"
            "Пасля гэтага проста пішы мне, што з'еў, — я ўсё палічу."
        ),
        "profile_view": (
            "👤 Твой профіль:\n\n"
            "Пол: {gender}\n"
            "Узрост: {age} гадоў\n"
            "Рост: {height} см\n"
            "Вага: {weight} кг\n"
            "Актыўнасць: {activity_label}\n"
            "Мэта: {goal_label}\n"
            "Норма: {daily_norm} ккал/дзень\n\n"
            "Каб змяніць дадзеныя, адпраў /reset"
        ),
        "ask_gender": "👤 Укажы свой пол:",
        "btn_male": "👨 Мужчынскі",
        "btn_female": "👩 Жаночы",
        "err_gender": "Калі ласка, абяры пол з дапамогай кнопак.",
        "ask_age": "📅 Колькі табе гадоў?",
        "err_age": "Увядзі карэктны ўзрост — цэлае лік ад 10 да 120.",
        "ask_height": "📏 Рост у сантыметрах? (напрыклад: 175)",
        "err_height": "Увядзі рост у сантыметрах — лік ад 100 да 250.",
        "ask_weight": "⚖️ Вага ў кілаграмах? (напрыклад: 70)",
        "err_weight": "Увядзі вагу ў кілаграмах — лік ад 30 да 300.",
        "ask_activity": (
            "🏃 Абяры ўзровень фізічнай актыўнасці:\n\n"
            "🪑 Сядзячы — офіс, амаль няма нагрузак\n"
            "🚶 Лёгкі — прагулкі, 1–3 трэніроўкі ў тыдзень\n"
            "🏋️ Умераны — 3–5 трэніровак у тыдзень\n"
            "🔥 Высокі — 6–7 трэніровак у тыдзень\n"
            "⚡ Вельмі высокі — фізічная праца або 2 трэніроўкі ў дзень"
        ),
        "btn_activity_sedentary": "🪑 Сядзячы",
        "btn_activity_light": "🚶 Лёгкі",
        "btn_activity_moderate": "🏋️ Умераны",
        "btn_activity_high": "🔥 Высокі",
        "btn_activity_very_high": "⚡ Вельмі высокі",
        "err_activity": "Калі ласка, абяры ўзровень актыўнасці з кнопак.",
        "ask_goal": "🎯 Якая ў цябе мэта?",
        "btn_goal_maintain": "⚖️ Падтрыманне вагі",
        "btn_goal_deficit": "📉 Схуданне (дэфіцыт)",
        "btn_goal_surplus": "📈 Набор масы (профіцыт)",
        "err_goal": "Калі ласка, абяры мэту з кнопак.",
        "ask_goal_percent": (
            "📉 На колькі адсоткаў змяніць каларыйнасць?\n\n"
            "Рэкамендуецца: 10–20% для мяккага эфекту, да 30% — для актыўнага."
        ),
        "err_goal_percent": "Увядзі лік ад 1 да 50 (напрыклад: 15).",
        "profile_saved": "✅ Профіль захаваны! Твая норма: {daily_norm} ккал/дзень.",
        "today_no_profile": "Спачатку наладзь профіль — націсні «👤 Профіль».",
        "today": (
            "📊 Сёння:\n\n"
            "З'едзена: {eaten} ккал\n"
            "Засталося: {remaining} ккал\n"
            "Норма: {norm} ккал"
        ),
        "history_empty": "Запісаў пакуль няма. Пачні адсочваць харчаванне!",
        "history_header": "📅 Гісторыя харчавання:\n\n",
        "history_row": "{date}: {kcal} ккал\n",
        "lang_choose": "🌍 Абяры мову:",
        "lang_changed": "✅ Мова зменена на {lang_name}.",
        "food_hint": "Напішы, што з'еў і колькі калорый, напрыклад:\n«грэчка 350» або проста «500»",
        "food_added": "✅ +{calories} ккал\nСёння: {eaten} ккал  |  Засталося: {remaining} ккал",
        "err_zero_cal": "❌ Калорый павінна быць больш за нуль.",
        "gender_male": "Мужчынскі",
        "gender_female": "Жаночы",
        "goal_maintain": "Падтрыманне вагі",
        "goal_deficit": "Схуданне −{pct}%",
        "goal_surplus": "Набор масы +{pct}%",
        "activity_sedentary": "Сядзячы (1.2)",
        "activity_light": "Лёгкі (1.375)",
        "activity_moderate": "Умераны (1.55)",
        "activity_high": "Высокі (1.725)",
        "activity_very_high": "Вельмі высокі (1.9)",
    },
}

LANG_NAMES = {
    "ru": "Русский", "en": "English", "uk": "Українська",
    "es": "Español", "de": "Deutsch", "fr": "Français", "be": "Беларуская",
}

# Maps button text → internal value for gender/goal, keyed by lang
_GENDER_MAP = {lang: {v[f"btn_male"]: "male", v[f"btn_female"]: "female"} for lang, v in STRINGS.items()}
_GOAL_MAP = {
    lang: {
        v["btn_goal_maintain"]: "maintain",
        v["btn_goal_deficit"]: "deficit",
        v["btn_goal_surplus"]: "surplus",
    }
    for lang, v in STRINGS.items()
}
_ACTIVITY_MAP = {
    lang: {
        v["btn_activity_sedentary"]: 1.2,
        v["btn_activity_light"]: 1.375,
        v["btn_activity_moderate"]: 1.55,
        v["btn_activity_high"]: 1.725,
        v["btn_activity_very_high"]: 1.9,
    }
    for lang, v in STRINGS.items()
}
_ACTIVITY_KEYS = {1.2: "activity_sedentary", 1.375: "activity_light", 1.55: "activity_moderate",
                  1.725: "activity_high", 1.9: "activity_very_high"}

_BTN_PROFILE = {v["btn_main_profile"] for v in STRINGS.values()}
_BTN_TODAY   = {v["btn_main_today"]   for v in STRINGS.values()}
_BTN_HISTORY = {v["btn_main_history"] for v in STRINGS.values()}
_BTN_LANG    = {v["btn_main_lang"]    for v in STRINGS.values()}


def t(lang: str, key: str, **kwargs) -> str:
    text = STRINGS.get(lang, STRINGS["ru"]).get(key, STRINGS["ru"].get(key, key))
    return text.format(**kwargs) if kwargs else text


def get_user_lang(tg_id: int) -> str:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.tg_id == tg_id).first()
        return (user.language or "ru") if user else "ru"
    finally:
        db.close()


# ====================== MODELS ======================

def calculate_daily_norm(gender, age, height, weight, activity, goal_type, goal_percent):
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    tdee = bmr * activity
    if goal_type == "deficit":
        return tdee * (1 - goal_percent / 100)
    elif goal_type == "surplus":
        return tdee * (1 + goal_percent / 100)
    return tdee


class ProfileStates(StatesGroup):
    gender = State()
    age = State()
    height = State()
    weight = State()
    activity = State()
    goal_type = State()
    goal_percent = State()


# ====================== KEYBOARDS ======================

def main_kb(lang: str) -> ReplyKeyboardMarkup:
    s = STRINGS.get(lang, STRINGS["ru"])
    buttons = [
        [KeyboardButton(text=s["btn_main_profile"]), KeyboardButton(text=s["btn_main_today"])],
        [KeyboardButton(text=s["btn_main_history"]), KeyboardButton(text=s["btn_main_lang"])],
    ]
    if MINI_APP_URL:
        buttons.append([KeyboardButton(text=s["btn_main_app"], web_app=WebAppInfo(url=MINI_APP_URL))])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, persistent=True)


def gender_kb(lang: str) -> ReplyKeyboardMarkup:
    s = STRINGS.get(lang, STRINGS["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=s["btn_male"]), KeyboardButton(text=s["btn_female"])]],
        resize_keyboard=True,
    )


def activity_kb(lang: str) -> ReplyKeyboardMarkup:
    s = STRINGS.get(lang, STRINGS["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=s["btn_activity_sedentary"]), KeyboardButton(text=s["btn_activity_light"])],
            [KeyboardButton(text=s["btn_activity_moderate"]), KeyboardButton(text=s["btn_activity_high"])],
            [KeyboardButton(text=s["btn_activity_very_high"])],
        ],
        resize_keyboard=True,
    )


def goal_kb(lang: str) -> ReplyKeyboardMarkup:
    s = STRINGS.get(lang, STRINGS["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=s["btn_goal_maintain"])],
            [KeyboardButton(text=s["btn_goal_deficit"]), KeyboardButton(text=s["btn_goal_surplus"])],
        ],
        resize_keyboard=True,
    )


def lang_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang_uk")],
        [InlineKeyboardButton(text="🇪🇸 Español", callback_data="lang_es")],
        [InlineKeyboardButton(text="🇩🇪 Deutsch", callback_data="lang_de")],
        [InlineKeyboardButton(text="🇫🇷 Français", callback_data="lang_fr")],
        [InlineKeyboardButton(text="🇧🇾 Беларуская", callback_data="lang_be")],
    ])


def fmt_gender(lang: str, gender: str) -> str:
    key = "gender_male" if gender == "male" else "gender_female"
    return t(lang, key)


def fmt_goal(lang: str, goal_type: str, goal_percent: float) -> str:
    if goal_type == "deficit":
        return t(lang, "goal_deficit", pct=int(goal_percent))
    if goal_type == "surplus":
        return t(lang, "goal_surplus", pct=int(goal_percent))
    return t(lang, "goal_maintain")


def fmt_activity(lang: str, activity: float) -> str:
    key = _ACTIVITY_KEYS.get(activity, "activity_moderate")
    return t(lang, key)


# ====================== /start ======================

@dp.message(Command("start"))
async def start_command(message: Message):
    lang = get_user_lang(message.from_user.id)
    await message.answer(t(lang, "start"), reply_markup=main_kb(lang))


# ====================== ПРОФИЛЬ ======================

@dp.message(F.text.in_(_BTN_PROFILE))
async def profile_button(message: Message, state: FSMContext):
    lang = get_user_lang(message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.tg_id == message.from_user.id).first()
        if user:
            await message.answer(
                t(lang, "profile_view",
                  gender=fmt_gender(lang, user.gender or "male"),
                  age=user.age,
                  height=user.height,
                  weight=user.weight,
                  activity_label=fmt_activity(lang, user.activity or 1.55),
                  goal_label=fmt_goal(lang, user.goal_type or "maintain", user.goal_percent or 0),
                  daily_norm=int(user.daily_norm)),
                reply_markup=main_kb(lang),
            )
            return
    finally:
        db.close()

    await state.set_state(ProfileStates.gender)
    await state.update_data(lang=lang)
    await message.answer(t(lang, "ask_gender"), reply_markup=gender_kb(lang))


@dp.message(Command("reset"))
async def reset_command(message: Message, state: FSMContext):
    lang = get_user_lang(message.from_user.id)
    await state.set_state(ProfileStates.gender)
    await state.update_data(lang=lang)
    await message.answer(t(lang, "ask_gender"), reply_markup=gender_kb(lang))


# ====================== FSM ======================

@dp.message(ProfileStates.gender)
async def process_gender(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    gender = _GENDER_MAP.get(lang, {}).get(message.text)
    if gender is None:
        await message.answer(t(lang, "err_gender"), reply_markup=gender_kb(lang))
        return
    await state.update_data(gender=gender)
    await state.set_state(ProfileStates.age)
    await message.answer(t(lang, "ask_age"), reply_markup=main_kb(lang))


@dp.message(ProfileStates.age)
async def process_age(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    try:
        age = int(message.text.strip())
        if age < 10 or age > 120:
            raise ValueError
    except ValueError:
        await message.answer(t(lang, "err_age"))
        return
    await state.update_data(age=age)
    await state.set_state(ProfileStates.height)
    await message.answer(t(lang, "ask_height"))


@dp.message(ProfileStates.height)
async def process_height(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    try:
        height = float(message.text.strip().replace(",", "."))
        if height < 100 or height > 250:
            raise ValueError
    except ValueError:
        await message.answer(t(lang, "err_height"))
        return
    await state.update_data(height=height)
    await state.set_state(ProfileStates.weight)
    await message.answer(t(lang, "ask_weight"))


@dp.message(ProfileStates.weight)
async def process_weight(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    try:
        weight = float(message.text.strip().replace(",", "."))
        if weight < 30 or weight > 300:
            raise ValueError
    except ValueError:
        await message.answer(t(lang, "err_weight"))
        return
    await state.update_data(weight=weight)
    await state.set_state(ProfileStates.activity)
    await message.answer(t(lang, "ask_activity"), reply_markup=activity_kb(lang))


@dp.message(ProfileStates.activity)
async def process_activity(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    activity = _ACTIVITY_MAP.get(lang, {}).get(message.text)
    if activity is None:
        await message.answer(t(lang, "err_activity"), reply_markup=activity_kb(lang))
        return
    await state.update_data(activity=activity)
    await state.set_state(ProfileStates.goal_type)
    await message.answer(t(lang, "ask_goal"), reply_markup=goal_kb(lang))


@dp.message(ProfileStates.goal_type)
async def process_goal_type(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    goal_type = _GOAL_MAP.get(lang, {}).get(message.text)
    if goal_type is None:
        await message.answer(t(lang, "err_goal"), reply_markup=goal_kb(lang))
        return
    await state.update_data(goal_type=goal_type)
    if goal_type == "maintain":
        await state.update_data(goal_percent=0)
        await _save_profile(message, state)
    else:
        await state.set_state(ProfileStates.goal_percent)
        await message.answer(t(lang, "ask_goal_percent"), reply_markup=main_kb(lang))


@dp.message(ProfileStates.goal_percent)
async def process_goal_percent(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    try:
        pct = float(message.text.strip().replace(",", "."))
        if pct <= 0 or pct > 50:
            raise ValueError
    except ValueError:
        await message.answer(t(lang, "err_goal_percent"))
        return
    await state.update_data(goal_percent=pct)
    await _save_profile(message, state)


async def _save_profile(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    db = SessionLocal()
    try:
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
        user.language = lang
        if not user.units:
            user.units = "metric"
        user.daily_norm = calculate_daily_norm(
            user.gender, user.age, user.height, user.weight,
            user.activity, user.goal_type, user.goal_percent,
        )
        db.commit()
        daily_norm = int(user.daily_norm)
    finally:
        db.close()

    await state.clear()
    await message.answer(t(lang, "profile_saved", daily_norm=daily_norm), reply_markup=main_kb(lang))


# ====================== СЕГОДНЯ ======================

@dp.message(F.text.in_(_BTN_TODAY))
async def today_button(message: Message):
    lang = get_user_lang(message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.tg_id == message.from_user.id).first()
        if not user:
            await message.answer(t(lang, "today_no_profile"), reply_markup=main_kb(lang))
            return
        logs = db.query(Log).filter(Log.tg_id == message.from_user.id, Log.date == date.today()).all()
        total = sum(l.calories for l in logs)
        norm = int(user.daily_norm)
    finally:
        db.close()

    await message.answer(
        t(lang, "today", eaten=int(total), remaining=int(norm - total), norm=norm),
        reply_markup=main_kb(lang),
    )


# ====================== ИСТОРИЯ ======================

@dp.message(F.text.in_(_BTN_HISTORY))
async def history_button(message: Message):
    lang = get_user_lang(message.from_user.id)
    db = SessionLocal()
    try:
        logs = db.query(Log).filter(Log.tg_id == message.from_user.id).order_by(Log.date.desc()).all()
        result = {}
        for log in logs:
            d = log.date.isoformat()
            result[d] = result.get(d, 0) + log.calories
    finally:
        db.close()

    if not result:
        await message.answer(t(lang, "history_empty"), reply_markup=main_kb(lang))
        return

    text = t(lang, "history_header")
    for d in sorted(result.keys(), reverse=True):
        text += t(lang, "history_row", date=d, kcal=int(result[d]))
    await message.answer(text, reply_markup=main_kb(lang))


# ====================== ЯЗЫК ======================

@dp.message(F.text.in_(_BTN_LANG))
async def lang_button(message: Message):
    lang = get_user_lang(message.from_user.id)
    await message.answer(t(lang, "lang_choose"), reply_markup=lang_inline_kb())


@dp.callback_query(F.data.startswith("lang_"))
async def lang_callback(callback: CallbackQuery):
    new_lang = callback.data.split("_", 1)[1]
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.tg_id == callback.from_user.id).first()
        if user:
            user.language = new_lang
            db.commit()
        # If no profile yet, we can't persist — that's fine, it'll be set on profile save.
    finally:
        db.close()

    lang_name = LANG_NAMES.get(new_lang, new_lang)
    await callback.message.edit_text(t(new_lang, "lang_changed", lang_name=lang_name))
    await callback.message.answer(t(new_lang, "lang_changed", lang_name=lang_name), reply_markup=main_kb(new_lang))
    await callback.answer()


# ====================== БЫСТРЫЙ ЛОГ ======================

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_food(message: Message, state: FSMContext):
    if await state.get_state() is not None:
        return

    lang = get_user_lang(message.from_user.id)
    text = message.text.strip()
    numbers = re.findall(r"\d+(?:[.,]\d+)?", text)
    if not numbers:
        await message.answer(t(lang, "food_hint"), reply_markup=main_kb(lang))
        return

    calories = float(numbers[0].replace(",", "."))
    if calories <= 0:
        await message.answer(t(lang, "err_zero_cal"))
        return

    db = SessionLocal()
    try:
        db.add(Log(tg_id=message.from_user.id, food_name=text[:100], calories=calories, date=date.today()))
        db.commit()

        user = db.query(User).filter(User.tg_id == message.from_user.id).first()
        today_logs = db.query(Log).filter(Log.tg_id == message.from_user.id, Log.date == date.today()).all()
        total_today = sum(l.calories for l in today_logs)
        norm = user.daily_norm if user else 2000
    finally:
        db.close()

    await message.answer(
        t(lang, "food_added",
          calories=int(calories),
          eaten=int(total_today),
          remaining=int(norm - total_today)),
        reply_markup=main_kb(lang),
    )


# ====================== ЗАПУСК ======================

async def main():
    print("🤖 Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
