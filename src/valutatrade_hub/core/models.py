"""Модели: User, Wallet, Portfolio."""

from __future__ import annotations

import hashlib
import math
import secrets
from datetime import datetime
from typing import Any


def _hash_password(password: str, salt: str) -> str:
    # Хэш
    return hashlib.sha256(f"{password}{salt}".encode("utf-8")).hexdigest()


def _ensure_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# пользователь
class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime | str,
    ) -> None:
        self._user_id = int(user_id)
        self.username = username  # через сеттер с проверкой
        self._hashed_password = str(hashed_password)
        self._salt = str(salt)
        self._registration_date = _ensure_datetime(registration_date)

        if not self._salt:
            raise ValueError("Соль (salt) не может быть пустой.")
        if not self._hashed_password:
            raise ValueError("Хеш пароля не может быть пустым.")

    @staticmethod
    def generate_salt() -> str:
        # уникальная соль для пользователя
        return secrets.token_hex(8)

    @classmethod
    def create_new(
        cls,
        user_id: int,
        username: str,
        password: str,
        registration_date: datetime | None = None,
    ) -> "User":
        if registration_date is None:
            registration_date = datetime.now()
        salt = cls.generate_salt()
        hashed = _hash_password(password, salt)
        return cls(
            user_id=user_id,
            username=username,
            hashed_password=hashed,
            salt=salt,
            registration_date=registration_date,
        )

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if value is None:
            raise ValueError("Имя пользователя не может быть пустым.")
        name = str(value).strip()
        if not name:
            raise ValueError("Имя пользователя не может быть пустым.")
        self._username = name

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    def get_user_info(self) -> dict[str, Any]:
        # информация о пользователе без пароля
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(timespec="seconds"),
        }

    def verify_password(self, password: str) -> bool:
        if password is None:
            return False
        hashed = _hash_password(str(password), self._salt)
        return hashed == self._hashed_password

    def change_password(self, new_password: str) -> None:
        if new_password is None:
            raise ValueError("Пароль должен быть не короче 4 символов.")
        pwd = str(new_password)
        if len(pwd) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")
        self._hashed_password = _hash_password(pwd, self._salt)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(timespec="seconds"),
        }


# кошелёк пользователя для одной конкретной валюты
class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        code = str(currency_code).strip().upper()
        if not code:
            raise ValueError("Код валюты не может быть пустым.")
        self._currency_code = code
        self.balance = balance  # через property setter

    @property
    def currency_code(self) -> str:
        return self._currency_code

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not _is_number(value):
            raise ValueError("Баланс должен быть числом.")
        v = float(value)
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Баланс должен быть корректным числом.")
        if v < 0:
            raise ValueError("Баланс не может быть отрицательным.")
        self._balance = v

    def deposit(self, amount: float) -> None:
        # пополнение баланса
        if not _is_number(amount) or float(amount) <= 0:
            raise ValueError("Сумма должна быть положительным числом.")
        self.balance = self._balance + float(amount)

    def withdraw(self, amount: float) -> None:
        # cнятие средств (если баланс позволяет)
        if not _is_number(amount) or float(amount) <= 0:
            raise ValueError("Сумма должна быть положительным числом.")
        amt = float(amount)
        if amt > self._balance:
            raise ValueError("Недостаточно средств.")
        self.balance = self._balance - amt

    def get_balance_info(self) -> dict[str, Any]:
        # информация о текущем балансе
        return {"currency_code": self._currency_code, "balance": self._balance}

    def to_dict(self) -> dict[str, Any]:
        return {"currency_code": self._currency_code, "balance": self._balance}


# управление кошельками пользователя
class Portfolio:
    def __init__(self, user: User, wallets: dict[str, Wallet] | None = None) -> None:
        self._user = user
        self._user_id = user.user_id
        self._wallets: dict[str, Wallet] = wallets or {}

    @property
    def user(self) -> User:
        return self._user

    @property
    def wallets(self) -> dict[str, Wallet]:
        return dict(self._wallets)

    def add_currency(self, currency_code: str) -> Wallet:
        # добавляет новый кошелёк в портфель
        code = str(currency_code).strip().upper()
        if not code:
            raise ValueError("Код валюты не может быть пустым.")
        if code in self._wallets:
            raise ValueError("Кошелёк для этой валюты уже существует.")
        wallet = Wallet(currency_code=code, balance=0.0)
        self._wallets[code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Wallet:
        # возвращает объект по коду валюты
        code = str(currency_code).strip().upper()
        if code not in self._wallets:
            raise ValueError("Кошелёк не найден.")
        return self._wallets[code]

    def get_total_value(self, base_currency: str = "USD") -> float:
        # общая стоимость всех валют в базовой валюте

        base = str(base_currency).strip().upper()
        if not base:
            raise ValueError("Базовая валюта не может быть пустой.")

        fixed_rates: dict[tuple[str, str], float] = {
            ("EUR", "USD"): 1.0786,
            ("BTC", "USD"): 59337.21,
            ("RUB", "USD"): 0.01016,
            ("ETH", "USD"): 3720.00,
        }

        def rate(frm: str, to: str) -> float:
            if frm == to:
                return 1.0
            direct = fixed_rates.get((frm, to))
            if direct is not None:
                return direct
            inverse = fixed_rates.get((to, frm))
            if inverse is not None and inverse != 0:
                return 1.0 / inverse
            raise ValueError(f"Курс {frm}->{to} недоступен.")

        total = 0.0
        for code, wallet in self._wallets.items():
            total += wallet.balance * rate(code, base)
        return total

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self._user_id,
            "wallets": {code: w.to_dict() for code, w in self._wallets.items()},
        }
