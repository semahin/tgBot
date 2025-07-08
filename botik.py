from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
import requests
import os
import pandas as pd
from db import init_db, save_purchase, get_user_purchase_by_index, delete_purchase
from ML import filter_semantically

init_db()
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ITEMS_PER_PAGE = 5

CSV_URL = "https://zakupki.gov.ru/epz/order/orderCsvSettings/download.html?morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber=1&sortDirection=false&recordsPerPage=_10&showLotsInfoHidden=false&savedSearchSettingsIdHidden=setting_order_kwysrk2v&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&ca=on&pc=on&pa=on&currencyIdGeneral=-1&customerPlace=5277376%2C5277374&customerPlaceCodes=73000000000%2C63000000000&okpd2Ids=8874163%2C8874162%2C8874161&okpd2IdsCodes=63.9%2C63.1%2C62.0&OrderPlacementSmallBusinessSubject=on&OrderPlacementRnpData=on&OrderPlacementExecutionRequirement=on&orderPlacement94_0=0&orderPlacement94_1=0&orderPlacement94_2=0&from=1&to=500&placementCsv=true&registryNumberCsv=true&stepOrderPlacementCsv=true&methodOrderPurchaseCsv=true&nameOrderCsv=true&purchaseNumbersCsv=true&numberLotCsv=true&nameLotCsv=true&maxContractPriceCsv=true&currencyCodeCsv=true&maxPriceContractCurrencyCsv=true&currencyCodeContractCurrencyCsv=true&scopeOkdpCsv=true&scopeOkpdCsv=true&scopeOkpd2Csv=true&scopeKtruCsv=true&ea615ItemCsv=true&customerNameCsv=true&organizationOrderPlacementCsv=true&publishDateCsv=true&lastDateChangeCsv=true&startDateRequestCsv=true&endDateRequestCsv=true&ea615DateCsv=true&featureOrderPlacementCsv=true"

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📄 Показать все улсуги", callback_data='show_csv')],
        [InlineKeyboardButton("📄 Показать ИТ улсуги", callback_data='show_filtered_csv')],
        [InlineKeyboardButton("📥 Получить CSV файл", callback_data='get_csv')],
        [InlineKeyboardButton("📋 Мой список", callback_data='show_saved')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "show_csv":
        await send_csv_row(update, context, index=0, is_edit=False)
    
    elif data == "show_f_csv":
        await send_filtered_csv_row(update, context, index=0, is_edit=False)
    
    elif data == "get_csv":
        await get_csv(update, context)

    elif data == "show_saved":
        await show_saved(update, context)

def load_csv_rows():
    try:
        df = pd.read_csv("zakupki_export.csv", sep=";", encoding="windows-1251")
        return df
    except Exception:
        return pd.DataFrame()
    
def get_csv_row(index: int):
    df = load_csv_rows()
    total = len(df)
    if 0 <= index < total:
        return df.iloc[index], total
    return None, total

async def send_csv_row(update, context, index: int, is_edit: bool):
    row, total = get_csv_row(index)

    if row is None:
        message = "❌ Запись не найдена."
        if is_edit:
            await update.callback_query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return

    title = row.get("Наименование закупки", "❓")
    price = row.get("Начальная (максимальная) цена контракта", "❓")
    customer = row.get("Наименование Заказчика", "❓")
    date = row.get("Дата размещения", "❓")
    deadline = row.get("Дата окончания подачи заявок", "❓")
    if deadline == "nan":
        deadline = "Неограничено"

    message = (
        f"📌 *{title}*\n"
        f"💰 {price} ₽\n"
        f"🏢 {customer}\n"
        f"📅 {date} → ⏳ {deadline}\n\n"
    )

    buttons = []

    if index > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"csv_{index - 1}"))
    buttons.append(InlineKeyboardButton("💾 Сохранить", callback_data=f"save_{index}"))
    if index + 1 < total:
        buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f"csv_{index + 1}"))

    reply_markup = InlineKeyboardMarkup([buttons])

    if not is_edit:
        if update.message:
            await update.message.reply_markdown(message.strip(), reply_markup=reply_markup)
        elif update.callback_query:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message.strip(),
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    else:
        await update.callback_query.message.edit_text(
            message.strip(),
            parse_mode="Markdown",
            reply_markup=reply_markup
        )


filtered_df = filter_semantically(df=load_csv_rows())

def get_filtered_csv_row(index: int):
    total = len(filtered_df)
    if 0 <= index < total:
        return filtered_df.iloc[index], total
    return None, total

async def send_filtered_csv_row(update, context, index: int = 0, is_edit=False):

    if filtered_df.empty:
        await update.message.reply_text("😔 Ничего не найдено по смыслу запроса.")
        return

    row = filtered_df.iloc[index]
    
    message = (
        f"📌 *{row['Наименование закупки']}*\n"
        f"💰 {row['Начальная (максимальная) цена контракта']} ₽\n"
        f"🏢 {row['Наименование Заказчика']}\n"
        f"📅 {row['Дата размещения']}"
    )

    buttons = []
    if index > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"fcsv_{index - 1}"))
    buttons.append(InlineKeyboardButton("💾 Сохранить", callback_data=f"fsave_{index}"))
    if index + 1 < len(filtered_df):
        buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f"fcsv_{index + 1}"))

    reply_markup = InlineKeyboardMarkup([buttons])

    if not is_edit:
        if update.message:
            await update.message.reply_markdown(message.strip(), reply_markup=reply_markup)
        elif update.callback_query:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message.strip(),
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    else:
        await update.callback_query.message.edit_text(
            message.strip(),
            parse_mode="Markdown",
            reply_markup=reply_markup
        )


async def show_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_csv_row(update, context, index=0, is_edit=False)

async def show_filtered_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_filtered_csv_row(update, context, index=0, is_edit=False)

async def handle_csv_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("csv_"):
        index = int(data.split("_")[1])
        await send_csv_row(update, context, index, is_edit=True)
    
    elif data.startswith("fcsv_"):
        index = int(data.split("_")[1])
        await send_filtered_csv_row(update, context, index, is_edit=True)

    elif data.startswith("save_"):
        index = int(data.split("_")[1])
        row, total = get_csv_row(index)

        if row is not None:
            user_id = query.from_user.id

            name = row.get("Наименование закупки", "❓")
            price = row.get("Начальная (максимальная) цена контракта", "❓")
            customer = row.get("Наименование Заказчика", "❓")
            date = row.get("Дата размещения", "❓")
            deadline = row.get("Дата окончания подачи заявок", "❓")

            save_purchase(user_id, name, price, customer, date, deadline)
            await query.answer("✅ Сохранено!")
        else:
            await query.answer("⚠️ Невозможно сохранить")

    elif data.startswith("fsave_"):
        index = int(data.split("_")[1])
        row, total = get_filtered_csv_row(index)

        if row is not None:
            user_id = query.from_user.id

            name = row.get("Наименование закупки", "❓")
            price = row.get("Начальная (максимальная) цена контракта", "❓")
            customer = row.get("Наименование Заказчика", "❓")
            date = row.get("Дата размещения", "❓")
            deadline = row.get("Дата окончания подачи заявок", "❓")

            save_purchase(user_id, name, price, customer, date, deadline)
            await query.answer("✅ Сохранено!")
        else:
            await query.answer("⚠️ Невозможно сохранить")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Чтобы получить список команд /list!")
    await menu(update, context)

async def get_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(CSV_URL, headers=headers)

    file_path = "zakupki_export.csv"
    with open(file_path, "wb") as f:
        f.write(response.content)

    doc = open(file_path, "rb")
    message = update.message or update.callback_query.message

    loading_msg = await message.reply_text("⏳ Загружаю CSV файл...")

    await message.reply_document(document=doc)

    await loading_msg.edit_text("✅ Файл успешно загружен и отправлен!")

async def save_first_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        df = pd.read_csv("zakupki_export.csv", sep=';', encoding='windows-1251')
        row = df.iloc[0]

        name = row.get("Наименование закупки", "❓")
        price = row.get("Начальная (максимальная) цена контракта", "❓")
        customer = row.get("Наименование Заказчика", "❓")
        date = row.get("Дата размещения", "❓")
        deadline = row.get("Дата окончания подачи заявок", "❓")

        save_purchase(user_id, name, price, customer, date, deadline)

        await update.message.reply_text("✅ Сохранено в твой личный список!")

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def send_user_purchase(update, context, user_id: int, index: int, is_edit=False):
    row, total = get_user_purchase_by_index(user_id, index)

    if row is None:
        msg = "📭 У тебя нет сохранённых закупок." if index == 0 else "❌ Запись не найдена."
        if is_edit:
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    id, name, price, customer, date, deadline = row

    text = (
        f"📌 *{name}*\n"
        f"💰 {price} ₽\n"
        f"🏢 {customer}\n"
        f"📅 {date} → ⏳ {deadline}\n"
    )

    buttons = []
    if index > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"plist_{index - 1}"))
    buttons.append(InlineKeyboardButton("🗑 Удалить", callback_data=f"del_{id}_{index}"))
    if index + 1 < total:
        buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f"plist_{index + 1}"))

    markup = InlineKeyboardMarkup([buttons])

    if is_edit:
        await update.callback_query.edit_message_text(
            text.strip(), reply_markup=markup, parse_mode="Markdown"
        )
    else:
        await update.message.reply_markdown(text.strip(), reply_markup=markup)


async def show_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await send_user_purchase(update, context, user_id, index=0, is_edit=False)

async def handle_mylist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data.startswith("plist_"):
        index = int(data.split("_")[1])
        await send_user_purchase(update, context, user_id, index, is_edit=True)

    elif data.startswith("del_"):
        _, purchase_id, index_str = data.split("_")
        delete_purchase(user_id, int(purchase_id))
        await query.answer("🗑 Удалено!")
        new_index = int(index_str)
        await send_user_purchase(update, context, user_id, new_index, is_edit=True)


async def list_of_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - Начать работу\n/getcsv - Получить файл\n/show - Список всех услуг\n/showfiltered - Список ИТ услуг\n/mylist - Показать список сохраненных услуг\n/list - Список команд")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("getcsv", get_csv))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("show", show_csv))
app.add_handler(CommandHandler("showfiltered", show_filtered_csv))
app.add_handler(CallbackQueryHandler(handle_csv_callback, pattern="^(csv_|fcsv_|save_|fsave_)"))
app.add_handler(CommandHandler("save", save_first_csv))
app.add_handler(CommandHandler("mylist", show_saved))
app.add_handler(CallbackQueryHandler(handle_mylist_callback, pattern="^(plist_|del_)"))
app.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="^(show_csv|show_f_csv|get_csv|show_saved)$"))
app.add_handler(CommandHandler("list", list_of_commands))
app.add_handler(CommandHandler("menu", menu))

app.run_polling()