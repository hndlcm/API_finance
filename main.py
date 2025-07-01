import time
from datetime import datetime, timedelta
from facturow.factura import export_fakturownia_all_to_google_sheets
from facturow.bitfactura import export_bitfactura_invoices_to_google_sheets, export_bitfactura_all_to_google_sheets
from etherscan.etherscan import export_erc20_to_google_sheet
from tronscan.transactions import export_trc20_transactions_troscan_to_google_sheets
from check_payment_status import export_portmone_orders_full
from mono.mono import export_mono_transactions_to_google_sheets
from privat.privat import privat_export


def generate_date_ranges(start_date, end_date, delta_days=31):
    current_start = start_date
    while current_start < end_date:
        current_end = min(current_start + timedelta(days=delta_days - 1), end_date)
        yield current_start, current_end
        current_start = current_end + timedelta(days=1)


def main_loop():
    while True:
        try:
            print("🚀 Запускаємо експорт privat транзакцій...")
            privat_export()
            print("✅ privat експорт завершено.\n")
        except Exception as e:
            print(f"❌ Помилка при експорті privat: {e}\n")
        try:
            print("🚀 Запускаємо експорт mono транзакцій...")
            export_mono_transactions_to_google_sheets()
            print("✅ mono експорт завершено.\n")
        except Exception as e:
            print(f"❌ Помилка при експорті mono: {e}\n")

        try:
            print("🚀 Запускаємо експорт TRC20 транзакцій...")
            export_fakturownia_all_to_google_sheets()
            print("✅ TRC20 експорт завершено.\n")
        except Exception as e:
            print(f"❌ Помилка при експорті TRC20: {e}\n")

        try:
            print("🚀 Запускаємо експорт інвойсів Bitfactura...")
            export_bitfactura_all_to_google_sheets()
            print("✅ Експорт інвойсів завершено.\n")
        except Exception as e:
            print(f"❌ Помилка при експорті Bitfactura: {e}\n")

        try:
            export_erc20_to_google_sheet()
        except Exception as e:
            print(f"❌ Помилка при експорті ERC20: {e}")

        try:
            export_trc20_transactions_troscan_to_google_sheets()
        except Exception as e:
            print(f"❌ Помилка при експорті TRC20 Tronscan: {e}")

        try:
            print("🚀 Запускаємо експорт замовлень Portmone за останні 2 роки...")
            export_portmone_orders_full()

            print("✅ Експорт замовлень Portmone завершено.\n")
        except Exception as e:
            print(f"❌ Помилка при експорті Portmone: {e}\n")

        print("⏰ Чекаємо 1 годину до наступного запуску...\n")
        time.sleep(3600)


if __name__ == "__main__":
    main_loop()
