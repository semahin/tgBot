import requests
import os
import pandas as pd

csv_url = "https://zakupki.gov.ru/epz/order/orderCsvSettings/download.html?morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber=1&sortDirection=false&recordsPerPage=_10&showLotsInfoHidden=false&savedSearchSettingsIdHidden=setting_order_kwysrk2v&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&ca=on&pc=on&pa=on&currencyIdGeneral=-1&customerPlace=5277376%2C5277374&customerPlaceCodes=73000000000%2C63000000000&okpd2Ids=8874163%2C8874162%2C8874161&okpd2IdsCodes=63.9%2C63.1%2C62.0&OrderPlacementSmallBusinessSubject=on&OrderPlacementRnpData=on&OrderPlacementExecutionRequirement=on&orderPlacement94_0=0&orderPlacement94_1=0&orderPlacement94_2=0&from=1&to=500&placementCsv=true&registryNumberCsv=true&stepOrderPlacementCsv=true&methodOrderPurchaseCsv=true&nameOrderCsv=true&purchaseNumbersCsv=true&numberLotCsv=true&nameLotCsv=true&maxContractPriceCsv=true&currencyCodeCsv=true&maxPriceContractCurrencyCsv=true&currencyCodeContractCurrencyCsv=true&scopeOkdpCsv=true&scopeOkpdCsv=true&scopeOkpd2Csv=true&scopeKtruCsv=true&ea615ItemCsv=true&customerNameCsv=true&organizationOrderPlacementCsv=true&publishDateCsv=true&lastDateChangeCsv=true&startDateRequestCsv=true&endDateRequestCsv=true&ea615DateCsv=true&featureOrderPlacementCsv=true"

headers = {
    "User-Agent": "Mozilla/5.0",
}

response = requests.get(csv_url, headers=headers)

with open("zakupki_export.csv", "wb") as f:
    f.write(response.content)

print("Файл сохранён успешно!")
print("Файл сохранён в:", os.getcwd())

df = pd.read_csv("zakupki_export.csv", sep=";", encoding="cp1251")

print(df.columns.tolist())
# Преобразуем цену в числовой формат
df["Начальная цена"] = pd.to_numeric(df["Начальная цена"].str.replace(",", ".").str.replace(" ", ""), errors="coerce")

# Сортируем
top_zakupki = df.sort_values(by="Начальная цена", ascending=False).head(5)

# Формируем текстовую сводку
for i, row in top_zakupki.iterrows():
    print(f"💰 {row['Наименование']} — {row['Начальная цена']:.2f} ₽")
    print(f"📅 Размещено: {row['Дата размещения']}")
    print(f"🏢 Заказчик: {row['Заказчик']}")
    print(f"🔗 Номер: {row['Номер извещения']}")
    print("---")