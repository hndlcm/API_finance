import json

from pydantic import BaseModel, RootModel


class Item(BaseModel):
    name: str | None = None
    address: str | None = None
    api_key: str
    days: int
    payee_id: int | None = None


class PaymentConfig(RootModel[dict[str, list[Item]]]):
    pass


def load_config(file_name: str):
    with open(file_name, encoding="utf-8") as f:
        config = PaymentConfig.model_validate(json.load(f))
    return config
