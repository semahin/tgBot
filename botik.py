from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
import requests
import os
import pandas as pd
from db import init_db, save_purchase, get_user_purchases

init_db()
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ITEMS_PER_PAGE = 5

CSV_URL = "https://zakupki.gov.ru/epz/order/orderCsvSettings/download.html?morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber=1&sortDirection=false&recordsPerPage=_10&showLotsInfoHidden=false&savedSearchSettingsIdHidden=setting_order_kwysrk2v&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&ca=on&pc=on&pa=on&currencyIdGeneral=-1&customerPlace=5277376%2C5277374&customerPlaceCodes=73000000000%2C63000000000&okpd2Ids=8874163%2C8874162%2C8874161&okpd2IdsCodes=63.9%2C63.1%2C62.0&OrderPlacementSmallBusinessSubject=on&OrderPlacementRnpData=on&OrderPlacementExecutionRequirement=on&orderPlacement94_0=0&orderPlacement94_1=0&orderPlacement94_2=0&from=1&to=500&placementCsv=true&registryNumberCsv=true&stepOrderPlacementCsv=true&methodOrderPurchaseCsv=true&nameOrderCsv=true&purchaseNumbersCsv=true&numberLotCsv=true&nameLotCsv=true&maxContractPriceCsv=true&currencyCodeCsv=true&maxPriceContractCurrencyCsv=true&currencyCodeContractCurrencyCsv=true&scopeOkdpCsv=true&scopeOkpdCsv=true&scopeOkpd2Csv=true&scopeKtruCsv=true&ea615ItemCsv=true&customerNameCsv=true&organizationOrderPlacementCsv=true&publishDateCsv=true&lastDateChangeCsv=true&startDateRequestCsv=true&endDateRequestCsv=true&ea615DateCsv=true&featureOrderPlacementCsv=true"

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📄 Показать первую закупку", callback_data='csv_0')],
        [InlineKeyboardButton("📥 Получить CSV", callback_data='get_csv')],
        [InlineKeyboardButton("📋 Мой список", callback_data='mylist')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

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
        text = "❌ Запись не найдена."
        if is_edit:
            await update.callback_query.edit_message_text(text)
        else:
            await update.message.reply_text(text)
        return

    title = row.get("Наименование закупки", "❓")
    price = row.get("Начальная (максимальная) цена контракта", "❓")
    customer = row.get("Наименование Заказчика", "❓")
    date = row.get("Дата размещения", "❓")
    deadline = row.get("Дата окончания подачи заявок", "❓")

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

    if is_edit:
        await update.callback_query.edit_message_text(
            message.strip(),
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_markdown(message.strip(), reply_markup=reply_markup)

async def show_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_csv_row(update, context, index=0, is_edit=False)

async def handle_csv_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("csv_"):
        index = int(data.split("_")[1])
        await send_csv_row(update, context, index, is_edit=True)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Чтобы получить список команд /list!")
    await menu(update, context)

async def get_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(CSV_URL, headers=headers)

    file_path = "zakupki_export.csv"
    with open(file_path, "wb") as f:
        f.write(response.content)

    with open(file_path, "rb") as doc:
        await update.message.reply_document(document=doc)

    await update.message.reply_text("✅ Файл успешно отправлен!")

async def save_first_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import pandas as pd

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

async def show_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    rows = get_user_purchases(user_id)

    if not rows:
        await update.message.reply_text("📭 У тебя пока нет сохранённых закупок.")
        return

    message = ""
    for r in rows:
        message += (
            f"📌 *{r[0]}*\n"
            f"💰 {r[1]}\n"
            f"🏢 {r[2]}\n"
            f"📅 {r[3]} → ⏳ {r[4]}\n\n"
        )

    await update.message.reply_markdown(message.strip())

async def list_of_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - Начать работу\n/getcsv - Получить файл\n/showcsv - Список услуг\n/save - Сохранить услугу\n/mylist - Показать список сохраненных услуг\n/list - Список команд!")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("getcsv", get_csv))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("showcsv", show_csv))
app.add_handler(CallbackQueryHandler(handle_csv_callback, pattern="^(csv_|save_)"))
app.add_handler(CommandHandler("save", save_first_csv))
app.add_handler(CommandHandler("mylist", show_saved))
app.add_handler(CommandHandler("list", list_of_commands))
app.add_handler(CommandHandler("menu", menu))

app.run_polling()