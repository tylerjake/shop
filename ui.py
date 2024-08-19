from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import json
import os

# Чтение данных кнопок из файла
def read_buttons():
    with open('buttons.json', 'r', encoding='utf-8') as file:
        return json.load(file)

# Чтение содержимого кнопок из файла
def read_content():
    with open('content.json', 'r', encoding='utf-8') as file:
        return json.load(file)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        ['Меню']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Добро пожаловать! Нажмите 'Меню' для навигации.",
        reply_markup=reply_markup
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    buttons = read_buttons()
    keyboard = [
        [buttons['button1']['text']],
        [buttons['button2']['text']],
        [buttons['button3']['text']],
        ['Назад']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text('Выберите опцию:', reply_markup=reply_markup)

async def button1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    buttons = read_buttons()
    subbuttons = buttons.get("button1_subbuttons", [])
    keyboard = [[button['name']] for button in subbuttons]
    keyboard.append(['Назад'])
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text('Выберите бота:', reply_markup=reply_markup)

async def subbutton(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    buttons = read_buttons()
    subbuttons = buttons.get("button1_subbuttons", [])
    button_name = update.message.text
    for button in subbuttons:
        if button['name'] == button_name:
            reply_markup = None
            if button.get("buy_enabled"):
                keyboard = [[InlineKeyboardButton("Купить", callback_data=f"buy:{button_name}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(button['content'], reply_markup=reply_markup)
            if button.get("files"):
                for file_path in button["files"]:
                    with open(file_path, 'rb') as f:
                        await update.message.reply_document(document=InputFile(f, filename=os.path.basename(file_path)))
            return

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    button_name = query.data.split(":")[1]
    payment_url = f"https://example.com/payment?item={button_name}"
    await query.edit_message_text(text=f"Перейдите по ссылке для оплаты: {payment_url}")

    # Имитация успешной покупки с вызовом purchase_success
    await purchase_success(query.message, context, button_name)

async def purchase_success(message, context: ContextTypes.DEFAULT_TYPE, button_name: str) -> None:
    buttons = read_buttons()
    subbuttons = buttons.get("button1_subbuttons", [])
    for button in subbuttons:
        if button['name'] == button_name:
            purchase_data = button.get("purchase_data", {})
            
            # Отладочная информация
            print(f"Отправка данных для под-кнопки {button_name}: {purchase_data}")
            print(f"Текст для отправки: {purchase_data.get('text')}")
            print(f"Файлы для отправки: {purchase_data.get('files')}")
            
            if purchase_data:
                await message.reply_text(purchase_data.get("text", "Спасибо за покупку!"))
                if "files" in purchase_data and purchase_data["files"]:
                    for file_path in purchase_data["files"]:
                        if os.path.exists(file_path):
                            print(f"Отправка файла: {file_path}")
                            with open(file_path, 'rb') as f:
                                await message.reply_document(document=InputFile(f, filename=os.path.basename(file_path)))
                        else:
                            print(f"Файл {file_path} не найден!")
                else:
                    print(f"Нет файлов для отправки для под-кнопки {button_name}")
            else:
                print(f"Нет данных для под-кнопки {button_name}")
            break

async def button2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    content = read_content()
    keyboard = [['Назад']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(content['content2'], reply_markup=reply_markup)

async def button3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    content = read_content()
    keyboard = [['Назад']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(content['content3'], reply_markup=reply_markup)

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)

def main() -> None:
    token = '6557871997:AAEBNRd66RoIKM6P3FuJoIgEju03H3A8U1Y'
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text(["Меню"]), menu))
    
    buttons = read_buttons()
    app.add_handler(MessageHandler(filters.Text(buttons['button1']['text']), button1))
    app.add_handler(MessageHandler(filters.Text(buttons['button2']['text']), button2))
    app.add_handler(MessageHandler(filters.Text(buttons['button3']['text']), button3))
    app.add_handler(MessageHandler(filters.Text("Назад"), back))

    # Динамическая обработка под-кнопок
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, subbutton))
    app.add_handler(CallbackQueryHandler(buy, pattern="^buy:"))

    app.run_polling()

if __name__ == '__main__':
    main()
