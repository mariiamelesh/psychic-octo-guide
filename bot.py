from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import random
import json
import os

BOT_TOKEN = "8586623169:AAEv1lbfMRbeVBDh1sQ2FtCiydy7V2TSOa0"

#логуання
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

#робимо менюшку з кнопок
menu_keyboard = [
    ["Почати", "Рандомний тест"],
    ["Мій рейтинг", "Помилковий тест"]
]
test_keyboard = [
    ["1", "2"],
    ["3", "4"]
]
menu_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)
test_markup = ReplyKeyboardMarkup(test_keyboard, resize_keyboard=True)

#беремо наші питання з джейсон-файлу
with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

#читаємо наш файл з інфою про користувача. Якщо про нього немає інфи, то призначаємо пусту базу
if os.path.exists("users_info.json"):
    with open("users_info.json", "r", encoding="utf-8") as f:
        USERS = json.load(f)
else:
    USERS = {}

#вписуємо інфу про користувача у цьому ж джейсон файлі
def save_users():
    with open("users_info.json", "w", encoding="utf-8") as f:
        json.dump(USERS, f, ensure_ascii=False, indent=4)

#функція що надсилає питання в чат користувачеві.
async def send_question(chat_id, context, question_text, question_data):
    context.user_data["current_question"] = (question_text, question_data)

    #варіанти відповідей вигляду - (1. а)
    options = "\n".join(
        [f"{i + 1}. {opt}" for i, opt in enumerate(question_data["options"])]
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"{question_text}\n{options}", # "питання" /n 1. а /n...
        reply_markup=test_markup
    )


#старт
async def flash_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in USERS:
        USERS[user_id] = {
            "amount_of_tests": 0,
            "right_answers": 0,
            "false_tests": {}
        }
        save_users()

    await update.message.reply_text(
        "Вітаю. Оберіть дію з меню.",
        reply_markup=menu_markup
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    USERS.setdefault(user_id, {
        "amount_of_tests": 0,
        "right_answers": 0,
        "false_tests": {}
    })

    if text == "Почати":
        await update.message.reply_text("Оберіть тест.")

    elif text == "Рандомний тест":
        question_text, question_data = random.choice(list(QUESTIONS.items()))
        await send_question(update.effective_chat.id, context, question_text, question_data)

    elif text in ["1", "2", "3", "4"]:
        if "current_question" not in context.user_data:
            await update.message.reply_text("Спочатку оберіть тест.")
            return

        question_text, question_data = context.user_data["current_question"]

        user_answer = question_data["options"][int(text) - 1]
        correct_answer = question_data["right_option"]

        USERS[user_id]["amount_of_tests"] += 1

        if user_answer == correct_answer:
            USERS[user_id]["right_answers"] += 1
            await update.message.reply_text("Відповідь правильна.")
        else:
            USERS[user_id]["false_tests"][question_text] = question_data
            await update.message.reply_text(
                f"Відповідь неправильна. Правильний варіант: {correct_answer}"
            )

        save_users()
        del context.user_data["current_question"]

    elif text == "Мій рейтинг":
        u = USERS[user_id]
        await update.message.reply_text(
            f"Кількість тестів: {u['amount_of_tests']}\n"
            f"Правильні відповіді: {u['right_answers']}"
        )

    elif text == "Помилковий тест":
        false_tests = USERS[user_id]["false_tests"]

        if not false_tests:
            await update.message.reply_text("Помилкових відповідей немає.")
            return
        question_text, question_data = random.choice(list(false_tests.items()))
        await send_question(update.effective_chat.id, context, question_text, question_data)

    else:
        await update.message.reply_text("Скористайтесь кнопками меню.")


application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.run_polling()
