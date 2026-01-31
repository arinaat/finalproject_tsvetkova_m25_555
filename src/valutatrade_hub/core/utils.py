# Вспомогательные функции проекта


from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

# Папка data в корне проекта (на одном уровне с pyproject.toml)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"


def data_file(filename: str) -> Path:
    return DATA_DIR / filename


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def normalize_currency_code(currency_code: str) -> str:
    if currency_code is None:
        raise ValueError("Код валюты не может быть пустым.")
    code = str(currency_code).strip().upper()
    if not code:
        raise ValueError("Код валюты не может быть пустым.")
    return code


def validate_username(username: str) -> str:
    if username is None:
        raise ValueError("Имя пользователя не может быть пустым.")
    name = str(username).strip()
    if not name:
        raise ValueError("Имя пользователя не может быть пустым.")
    return name


def validate_password(password: str) -> str:
    if password is None:
        raise ValueError("Пароль должен быть не короче 4 символов.")
    pwd = str(password)
    if len(pwd) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов.")
    return pwd


def validate_amount(amount: Any) -> float:
    if not _is_number(amount):
        raise ValueError("Сумма должна быть числом.")
    x = float(amount)
    if math.isnan(x) or math.isinf(x):
        raise ValueError("Сумма должна быть корректным числом.")
    if x <= 0:
        raise ValueError("Сумма должна быть больше 0.")
    return x


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


USERS_JSON = data_file("users.json")
PORTFOLIOS_JSON = data_file("portfolios.json")
RATES_JSON = data_file("rates.json")


def load_users() -> list[dict[str, Any]]:
    return read_json(USERS_JSON, default=[])


def save_users(users: list[dict[str, Any]]) -> None:
    write_json(USERS_JSON, users)


def load_portfolios() -> list[dict[str, Any]]:
    return read_json(PORTFOLIOS_JSON, default=[])


def save_portfolios(portfolios: list[dict[str, Any]]) -> None:
    write_json(PORTFOLIOS_JSON, portfolios)


def load_rates() -> dict[str, Any]:
    return read_json(RATES_JSON, default={"source": "LocalCache", "last_refresh": None})


def save_rates(rates: dict[str, Any]) -> None:
    write_json(RATES_JSON, rates)
