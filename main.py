import time
from datetime import datetime, timedelta
from facturow.factura import export_invoices_to_google_sheets
from facturow.bitfactura import export_bitfactura_invoices_to_google_sheets
from etherscan.etherscan import export_erc20_to_google_sheet
from tronscan.transactions import export_trc20_transactions_troscan_to_google_sheets
from check_payment_status import export_portmone_orders

def generate_date_ranges(start_date, end_date, delta_days=31):
    current_start = start_date
    while current_start < end_date:
        current_end = min(current_start + timedelta(days=delta_days - 1), end_date)
        yield current_start, current_end
        current_start = current_end + timedelta(days=1)

def main_loop():
    while True:
        print("🚀 Запускаємо експорт TRC20 транзакцій...")
        export_invoices_to_google_sheets()
        print("✅ TRC20 експорт завершено.\n")

        print("🚀 Запускаємо експорт інвойсів Bitfactura...")
        export_bitfactura_invoices_to_google_sheets()
        print("✅ Експорт інвойсів завершено.\n")

        export_erc20_to_google_sheet()
        export_trc20_transactions_troscan_to_google_sheets()

        print("🚀 Запускаємо експорт замовлень Portmone за останні 2 роки...")

        end_date = datetime.today()
        start_date = end_date - timedelta(days=365 * 2)  # 2 роки тому

        for start, end in generate_date_ranges(start_date, end_date):
            start_str = start.strftime("%d.%m.%Y")
            end_str = end.strftime("%d.%m.%Y")
            print(f"  ↪ Обробка періоду {start_str} - {end_str}")
            export_portmone_orders(start_str, end_str)
            time.sleep(1)  # трохи почекати між запитами, щоб не перевантажити API

        print("✅ Експорт замовлень Portmone завершено.\n")

        print("⏰ Чекаємо 1 годину до наступного запуску...")
        time.sleep(3600)  # Пауза 3600 секунд (1 година)

if __name__ == "__main__":
    main_loop()
