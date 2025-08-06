import json
from pathlib import Path

from pydantic import BaseModel, RootModel


class PaymentItem(BaseModel):
    name: str | None = None
    address: str | None = None
    api_key: str
    days: int

    login: str | None = None
    password: str | None = None
    payee_id: int | None = None


class PaymentConfig(RootModel[dict[str, list[PaymentItem]]]):
    pass


def load_config(file_name: str | Path) -> PaymentConfig:
    with open(file_name, encoding="utf-8") as f:
        config = PaymentConfig.model_validate(json.load(f))
        return config
