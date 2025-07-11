import requests
import os
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from db import init_db, save_purchase, get_user_purchase_by_index, delete_purchase, get_new_records_from_db, save_scheduled_purchase, get_new_records_for_user, clear_scheduled_purchases
from ML import filter_semantically

init_db()
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ITEMS_PER_PAGE = 5

CSV_URL_NEEDED = "https://zakupki.gov.ru/epz/order/orderCsvSettings/download.html?morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber=1&sortDirection=false&recordsPerPage=_10&showLotsInfoHidden=false&savedSearchSettingsIdHidden=setting_order_kwysrk2v&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&ca=on&pc=on&pa=on&currencyIdGeneral=-1&customerPlace=5277376%2C5277374&customerPlaceCodes=73000000000%2C63000000000&okpd2Ids=8874163%2C8874162%2C8874161&okpd2IdsCodes=63.9%2C63.1%2C62.0&OrderPlacementSmallBusinessSubject=on&OrderPlacementRnpData=on&OrderPlacementExecutionRequirement=on&orderPlacement94_0=0&orderPlacement94_1=0&orderPlacement94_2=0&from=1&to=500&placementCsv=true&registryNumberCsv=true&stepOrderPlacementCsv=true&methodOrderPurchaseCsv=true&nameOrderCsv=true&purchaseNumbersCsv=true&numberLotCsv=true&nameLotCsv=true&maxContractPriceCsv=true&currencyCodeCsv=true&maxPriceContractCurrencyCsv=true&currencyCodeContractCurrencyCsv=true&scopeOkdpCsv=true&scopeOkpdCsv=true&scopeOkpd2Csv=true&scopeKtruCsv=true&ea615ItemCsv=true&customerNameCsv=true&organizationOrderPlacementCsv=true&publishDateCsv=true&lastDateChangeCsv=true&startDateRequestCsv=true&endDateRequestCsv=true&ea615DateCsv=true&featureOrderPlacementCsv=true"
CSV_URL = "https://zakupki.gov.ru/epz/order/orderCsvSettings/download.html?searchString=&morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5%20%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber=1&sortDirection=false&recordsPerPage=_10&showLotsInfoHidden=false&savedSearchSettingsIdHidden=&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&ca=on&pc=on&pa=on&placingWayList=&selectedLaws=&priceFromGeneral=&priceFromGWS=&priceFromUnitGWS=&priceToGeneral=&priceToGWS=&priceToUnitGWS=&currencyIdGeneral=-1&publishDateFrom=&publishDateTo=&applSubmissionCloseDateFrom=&applSubmissionCloseDateTo=&customerIdOrg=&customerFz94id=&customerTitle=&okpd2Ids=&okpd2IdsCodes=&from=1&to=500&placementCsv=true&registryNumberCsv=true&stepOrderPlacementCsv=true&methodOrderPurchaseCsv=true&nameOrderCsv=true&purchaseNumbersCsv=true&numberLotCsv=true&nameLotCsv=true&maxContractPriceCsv=true&currencyCodeCsv=true&maxPriceContractCurrencyCsv=true&currencyCodeContractCurrencyCsv=true&scopeOkdpCsv=true&scopeOkpdCsv=true&scopeOkpd2Csv=true&scopeKtruCsv=true&ea615ItemCsv=true&customerNameCsv=true&organizationOrderPlacementCsv=true&publishDateCsv=true&lastDateChangeCsv=true&startDateRequestCsv=true&endDateRequestCsv=true&ea615DateCsv=true&featureOrderPlacementCsv=true"


def load_csv_rows():
    try:
        df = pd.read_csv("zakupki_export.csv", sep=";", encoding="windows-1251")
        return df
    except Exception as e:
        print(f"[load_csv_rows] ❌ Ошибка чтения CSV: {e}")
        return pd.DataFrame()
    
# def get_csv_row(index: int):
#     df = load_csv_rows()
#     total = len(df)
#     if 0 <= index < total:
#         return df.iloc[index], total
#     return None, total

def getu_csv_row(index: int, df):
    total = len(df)
    if 0 <= index < total:
        return df.iloc[index], total
    return None, total


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# ML block  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

df = load_csv_rows()

filtered_df = filter_semantically(df)

# def get_filtered_csv_row(index: int):
#     total = len(filtered_df)
#     if 0 <= index < total:
#         return filtered_df.iloc[index], total
#     return None, total

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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# DB block  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

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

        await update.message.reply_text("✅ Сохранено в Ваш личный список!")

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
        if update.message:
            await update.message.reply_markdown(text.strip(), reply_markup=markup)
        elif update.callback_query:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text.strip(),
                parse_mode="Markdown",
                reply_markup=markup
            )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# handlers block  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

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
        row, total = getu_csv_row(index, df) # --- df undefined

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
        row, total = getu_csv_row(index, df) # --- df undefined

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

    elif data.startswith("autofsave_"):
        index = int(data.split("_")[1])
        df = context.bot_data.get("scheduled_df")

        if df is None or index >= len(df):
            await query.answer("❌ Запись не найдена.")
            return

        row = df.iloc[index]
        user_id = query.from_user.id

        name = row.get("Наименование закупки", "❓")
        price = row.get("Начальная (максимальная) цена контракта", "❓")
        customer = row.get("Наименование Заказчика", "❓")
        date = row.get("Дата размещения", "❓")
        deadline = row.get("Дата окончания подачи заявок", "❓")

        save_purchase(user_id, name, price, customer, date, deadline)
        await query.answer("✅ Сохранено!")

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

async def handle_scheduled_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    data = query.data

    if data.startswith("sched_"):
        index = int(data.split("_")[1])
        await send_scheduled_csv_row(update, context, user_id, index, is_edit=True)

    elif data.startswith("ssave_"):
        index = int(data.split("_")[1])
        row = scheduled_df_by_user.get(user_id, pd.DataFrame()).iloc[index]
        if row is not None:
            save_purchase(
                user_id,
                row.get("Наименование закупки", "❓"),
                row.get("Начальная (максимальная) цена контракта", "❓"),
                row.get("Наименование Заказчика", "❓"),
                row.get("Дата размещения", "❓"),
                row.get("Дата окончания подачи заявок", "❓")
            )
            await query.answer("✅ Сохранено!")
        else:
            await query.answer("⚠️ Не удалось сохранить.")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# schedule block  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

scheduled_df_by_user = {}

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # df = load_csv_rows()

    if df.empty:
        await update.message.reply_text("⚠️ CSV не загружен.")
        return
    
    # scheduled_df_by_user[user_id] = pd.DataFrame()
    clear_scheduled_purchases(user_id)

    new_df = get_new_records_from_db(df, user_id)

    if new_df.empty:
        await update.message.reply_text("🟢 У Вас нет новых закупок.")
        return

    for _, row in new_df.iterrows():
        save_scheduled_purchase(row, user_id)

    scheduled_df_by_user[user_id] = new_df.reset_index(drop=True)

    await send_scheduled_csv_row(update, context, user_id, index=0, is_edit=False)

    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    context.job_queue.run_repeating(
        send_updates_job,
        interval=120,
        first=0,
        chat_id=chat_id,
        name=str(chat_id)
    )
    await update.message.reply_text("📬 Вы подписаны на автообновление каждый час.")

async def send_scheduled_csv_row(update, context, user_id: int, index: int, is_edit=False):
    df = scheduled_df_by_user.get(user_id)

    if df is None or df.empty or index >= len(df):
        message = "❌ Нечего показывать."
        if update and is_edit:
            await update.callback_query.edit_message_text(message)
        elif update and update.message:
            await update.message.reply_text(message)
        elif update and update.callback_query:
            await update.callback_query.message.reply_text(message)
        else:
            await context.bot.send_message(chat_id=user_id, text=message)
        return

    row = df.iloc[index]

    title = row.get("Наименование закупки", "❓")
    price = row.get("Начальная (максимальная) цена контракта", "❓")
    customer = row.get("Наименование Заказчика", "❓")
    date = row.get("Дата размещения", "❓")
    deadline = row.get("Дата окончания подачи заявок")
    if pd.isna(deadline) or not deadline:
        deadline = "Не указано"

    text = (
        f"📌 *{title}*\n"
        f"💰 {price} ₽\n"
        f"🏢 {customer}\n"
        f"📅 {date} → ⏳ {deadline}"
    )

    buttons = []
    if index > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"sched_{index - 1}"))
    buttons.append(InlineKeyboardButton("💾 Сохранить", callback_data=f"ssave_{index}"))
    if index + 1 < len(df):
        buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f"sched_{index + 1}"))
    reply_markup = InlineKeyboardMarkup([buttons])

    if update is None:
        await context.bot.send_message(
            chat_id=user_id,
            text=text.strip(),
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    elif not is_edit:
        if update.message:
            await update.message.reply_markdown(text.strip(), reply_markup=reply_markup)
        elif update.callback_query:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text.strip(),
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    else:
        await update.callback_query.message.edit_text(
            text.strip(),
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

async def send_updates_job(context):
    chat_id = context.job.chat_id
    user_id = chat_id

    # df = load_csv_rows()
    new_df = get_new_records_from_db(df, user_id)  # ← тут уже не чистим

    if new_df.empty:
        await context.bot.send_message(chat_id=chat_id, text="🟢 Новых закупок нет.")
        return
    
    for _, row in new_df.iterrows():
        save_scheduled_purchase(row, user_id)

    scheduled_df_by_user[user_id] = new_df.reset_index(drop=True)

    await context.bot.send_message(chat_id=chat_id, text="📬 Обнаружены новые закупки!")

    await send_scheduled_csv_row(
        update=None,
        context=context,
        user_id=user_id,
        index=0,
        is_edit=False
    )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# commands block  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Показать все улсуги", callback_data='show_csv')],
        [InlineKeyboardButton("Показать ИТ улсуги", callback_data='show_f_csv')],
        [InlineKeyboardButton("Получить CSV файл", callback_data='get_csv')],
        [InlineKeyboardButton("Мой список", callback_data='show_saved')],
        [InlineKeyboardButton("Подписаться на обновления", callback_data='schedule')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

async def list_of_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - Начать работу\n/getcsv - Получить файл\n/show - Список всех услуг\n/showfiltered - Список ИТ услуг\n/schedule - Подписаться на обновления\n/mylist - Показать список сохраненных услуг\n/list - Список команд")

async def show_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await send_user_purchase(update, context, user_id, index=0, is_edit=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Чтобы получить список команд /list!")
    await menu(update, context)

async def get_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(CSV_URL, headers=headers)

    file_path = "zakupki_export.csv"
    with open(file_path, "wb") as f:
        f.write(response.content)

    chat_id = update.effective_chat.id

    loading_msg = await context.bot.send_message(chat_id=chat_id, text="⏳ Загружаю CSV файл...")

    with open(file_path, "rb") as doc:
        await context.bot.send_document(chat_id=chat_id, document=doc)

    await loading_msg.edit_text("✅ Файл успешно загружен и отправлен!")

async def show_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_csv_row(update, context, index=0, is_edit=False)

async def send_csv_row(update, context, index: int, is_edit: bool):
    row, total = getu_csv_row(index) # --- df undefined

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

async def show_filtered_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_filtered_csv_row(update, context, index=0, is_edit=False)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# application block - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

async def silent_update_csv(context: ContextTypes.DEFAULT_TYPE):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(CSV_URL, headers=headers)
        with open("zakupki_export.csv", "wb") as f:
            f.write(response.content)
        df = load_csv_rows()
        print("CSV-файл обновлён, DataFrame загружен")
    except Exception as e:
        print(f"Ошибка фонового обновления CSV: {e}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("getcsv", get_csv))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("show", show_csv))
app.add_handler(CommandHandler("showfiltered", show_filtered_csv))
app.add_handler(CallbackQueryHandler(handle_csv_callback, pattern="^(csv_|fcsv_|save_|fsave_)"))
app.add_handler(CommandHandler("save", save_first_csv))
app.add_handler(CommandHandler("mylist", show_saved))
app.add_handler(CallbackQueryHandler(handle_mylist_callback, pattern="^(plist_|del_)"))
app.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="^(show_csv|show_f_csv|get_csv|show_saved|schedule)$"))
app.add_handler(CommandHandler("list", list_of_commands))
app.add_handler(CommandHandler("menu", menu))
app.add_handler(CommandHandler("schedule", schedule))
# app.add_handler(CommandHandler("showupnew", showupnew))
app.add_handler(CallbackQueryHandler(handle_scheduled_callback, pattern="^(sched_|ssave_)"))
app.job_queue.run_repeating(silent_update_csv, interval=100, first=5)

app.run_polling()