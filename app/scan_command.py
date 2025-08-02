from .settings import Settings


def scan_command(settings: Settings):
    pass

    # limiter = RateLimiter(max_calls=7, period=1)
    #
    # credentials = service_account.Credentials.from_service_account_file(
    #     str(BIG_QUERY_CRED_FILE)
    # )
    # client = bigquery.Client(
    #     credentials=credentials, project=credentials.project_id
    # )
    # logger.debug(credentials.project_id)
    # table_id = "fin-api-463108.finapi.fin-api-fin"


#    query = f"SELECT * FROM `{table_id}` LIMIT 1000"

#    df = client.query(query).to_dataframe()
#    print(df)

# tables = client.list_tables(dataset_id)
# for table in tables:
#     logger.debug(f"Table: {table.table_id}")
#     table_ref = client.get_table(f"{dataset_id}.{table.table_id}")
#     logger.debug(f"Schema for table {table.table_id}:")
#     for schema_field in table_ref.schema:
#         logger.debug(f" - {schema_field.name} ({
#         schema_field.field_type})")

# payment_config = load_config("app_data/config.json")
# privat_items = payment_config.root.get("PRIVAT", [])
# logger.debug(privat_items[0].api_key)
#
# token = privat_items[0].api_key
# api = PrivatApi(token)
#
# to_date_dt = datetime.now()
# from_date_dt = to_date_dt - timedelta(days=65)
#
# # r = api.fetch_all_balances()
# r = api.fetch_all_transactions(from_date_dt, to_date_dt)
# logger.debug(r)

# while True:
# try:
#     print("🚀 Запускаємо експорт privat транзакцій...")
#     privat_export()
#     print("✅ privat експорт завершено.\n")
# except Exception as e:
#     print(f"❌ Помилка при експорті privat: {e}\n")
# try:
#     print("🚀 Запускаємо експорт mono транзакцій...")
#     export_mono_transactions_to_google_sheets()
#     print("✅ mono експорт завершено.\n")
# except Exception as e:
#     print(f"❌ Помилка при експорті mono: {e}\n")
#
# try:
#     print("🚀 Запускаємо експорт TRC20 транзакцій...")
#     export_fakturownia_all_to_google_sheets()
#     print("✅ TRC20 експорт завершено.\n")
# except Exception as e:
#     print(f"❌ Помилка при експорті TRC20: {e}\n")
#
# try:
#     print("🚀 Запускаємо експорт інвойсів Bitfactura...")
#     export_bitfactura_all_to_google_sheets()
#     print("✅ Експорт інвойсів завершено.\n")
# except Exception as e:
#     print(f"❌ Помилка при експорті Bitfactura: {e}\n")
#
# try:
#     export_erc20_to_google_sheet()
# except Exception as e:
#     print(f"❌ Помилка при експорті ERC20: {e}")
#
# try:
#     export_trc20_transactions_troscan_to_google_sheets()
# except Exception as e:
#     print(f"❌ Помилка при експорті TRC20 Tronscan: {e}")
#
# try:
#     print(
#         "🚀 Запускаємо експорт замовлень Portmone за останні 2 роки..."
#     )
#     export_portmone_orders_full()
#
#     print("✅ Експорт замовлень Portmone завершено.\n")
# except Exception as e:
#     print(f"❌ Помилка при експорті Portmone: {e}\n")
#
# print("⏰ Чекаємо 1 годину до наступного запуску...\n")
# time.sleep(3600)
