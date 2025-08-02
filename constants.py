from pathlib import Path
from typing import Final

CURRENCY_CODES: Final[dict] = {
    980: "UAH",  # Українська гривня
    840: "USD",  # Долар США
    978: "EUR",  # Євро
    826: "GBP",  # Фунт стерлінгів
    985: "PLN",  # Польський злотий
}

BIG_QUERY_CRED_FILE: Final[Path] = Path(
    "app_data/fin-api-463108-7083ad9de650.json"
)

PAYMENT_CONFIG_FILE: Final[Path] = Path("app_data/config.json")
