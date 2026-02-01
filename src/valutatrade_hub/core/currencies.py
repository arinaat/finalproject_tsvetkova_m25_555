# Иерархия валют + реестр валют

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


def _validate_code(code: str) -> str:
    c = (code or "").strip().upper()
    if not (2 <= len(c) <= 5) or " " in c:
        raise ValueError(
            "Код валюты должен быть 2-5 символов, без пробелов, в верхнем регистре."
        )
    return c


def _validate_name(name: str) -> str:
    n = (name or "").strip()
    if not n:
        raise ValueError("Название валюты не должно быть пустым.")
    return n


@dataclass(frozen=True)
class Currency(ABC):
    #Абстрактная валюта

    name: str
    code: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _validate_name(self.name))
        object.__setattr__(self, "code", _validate_code(self.code))

    @abstractmethod
    def get_display_info(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class FiatCurrency(Currency):
    # Фиатная валюта

    issuing_country: str

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(
            self, "issuing_country", _validate_name(self.issuing_country)
        )

    def get_display_info(self) -> str:
        return f"[FIAT]{self.code} - {self.name} (Issuing: {self.issuing_country})"


@dataclass(frozen=True)
class CryptoCurrency(Currency):
    # Криптовалюта

    algorithm: str
    market_cap: float

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "algorithm", _validate_name(self.algorithm))
        if not isinstance(self.market_cap, (int, float)) or self.market_cap < 0:
            raise ValueError("market_cap должен быть числом >= 0.")

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO]{self.code} - {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


# Реестр валют
_CURRENCIES: dict[str, Currency] = {
    "USD": FiatCurrency(name="US Dollar", code="USD", issuing_country="United States"),
    "EUR": FiatCurrency(name="Euro", code="EUR", issuing_country="Eurozone"),
    "RUB": FiatCurrency(name="Russian Ruble", code="RUB", issuing_country="Russia"),
    "BTC": CryptoCurrency(
        name="Bitcoin", code="BTC", algorithm="SHA-256", market_cap=1.12e12
    ),
    "ETH": CryptoCurrency(
        name="Ethereum", code="ETH", algorithm="Ethash", market_cap=4.50e11
    ),
}


def get_currency(code: str) -> Currency:
    c = _validate_code(code)
    cur = _CURRENCIES.get(c)
    if cur is None:
        raise CurrencyNotFoundError(c)
    return cur
