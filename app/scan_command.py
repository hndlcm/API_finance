import logging

from google.cloud import bigquery
from google.oauth2 import service_account

from .bigquery_table.table import Table
from .payment_config import load_config
from .payments.mono.scanner import MonoScanner
from .payments.privat.scanner import PrivatScanner
from .schemas import TransactionRecord
from .settings import Settings

logger = logging.getLogger(__name__)


scanners = {
    PrivatScanner.KEY: PrivatScanner,
    MonoScanner.KEY: MonoScanner,
}


def scan_command(settings: Settings):
    payment_config = load_config(settings.payment_config_file)
    transactions = []
    logger.info("Scanning payment systems ...")
    for key, ScannerType in scanners.items():
        if items := payment_config.root.get(key):
            try:
                scanner = ScannerType(items)
                records: list[TransactionRecord] = scanner.scan()
                transactions.extend(records)
            except Exception as e:
                logger.error("%s %s", type(e), e)

    logger.info("Connecting to BigQuery ...")
    credentials = service_account.Credentials.from_service_account_file(
        str(settings.big_query_cred_file)
    )
    client = bigquery.Client(credentials.project_id, credentials)

    logger.info("Inserting and updating transactions in BigQuery table ...")
    table = Table(
        table_id=settings.big_query_table_id,
        pydantic_cls=TransactionRecord,
        primary_keys=["transaction_id", "bank_or_system"],
        client=client,
    )
    table.upsert_records(transactions)


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
