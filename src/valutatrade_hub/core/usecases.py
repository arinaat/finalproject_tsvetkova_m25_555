from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import InsufficientFundsError
from valutatrade_hub.core.models import Portfolio, User, Wallet
from valutatrade_hub.core.utils import (
    data_file,
    load_portfolios,
    load_rates,
    load_users,
    normalize_currency_code,
    read_json,
    save_portfolios,
    save_rates,
    save_users,
    validate_amount,
    validate_password,
    validate_username,
    write_json,
)
from valutatrade_hub.infra.decorators import log_action
from valutatrade_hub.infra.settings import SettingsLoader

#Курсы и кэш

CACHE_TTL_SECONDS = 300  # 5 минут


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    try:
        dt = datetime.fromisoformat(str(value))
        # если строка без таймзоны — считаем, что это UTC
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    except ValueError:
        return None


def _is_fresh(last_refresh: Any, ttl_seconds: int | None = None) -> bool:
    dt = _parse_iso_dt(last_refresh)
    if ttl_seconds is None:
        ttl_seconds = int(SettingsLoader().get("rates_ttl_seconds", 300))
    if ttl_seconds is None:
        ttl_seconds = int(SettingsLoader().get("rates_ttl_seconds", 300))
    if dt is None:
        return False
    return _now_utc() - dt <= timedelta(seconds=ttl_seconds)


def _refresh_rates_stub() -> dict[str, Any]:
    now = _now_utc().replace(microsecond=0).isoformat()

    rates = {
        "USD": 1.0,
        "EUR": 0.92,
        "RUB": 98.38,
        "BTC": 0.00001685,
        "ETH": 0.000268,
    }
    return {"source": "LocalStub", "last_refresh": now, "base": "USD", "rates": rates}


def ensure_rates_fresh() -> dict[str, Any]:
    #Возвращает актуальные курсы. Если кэш устарел — обновляет и сохраняет
    cache = load_rates()
    if not _is_fresh(cache.get("last_refresh")) or "rates" not in cache:
        cache = _refresh_rates_stub()
        save_rates(cache)
    return cache


def get_rate(from_currency: str, to_currency: str) -> dict[str, Any]:
    """Возвращает курс from->to и метаданные.

    Формат кэша (ensure_rates_fresh):
    - base="USD"
    - rates[CCY] = сколько CCY за 1 USD
    """
    from_code = get_currency(from_currency).code
    to_code = get_currency(to_currency).code

    # 1) Тождественный курс
    if from_code == to_code:
        return {
            "from": from_code,
            "to": to_code,
            "rate": 1.0,
            "source": "LocalCache",
            "last_refresh": None,
            "base": from_code,
        }

    data = ensure_rates_fresh()
    base = normalize_currency_code(data.get("base", "USD"))
    rates: dict[str, float] = data.get("rates", {})

    if not rates:
        raise ValueError(
            "Нет данных о курсах. Выполните update-rates или повторите позже."
        )

    # Нормализуем только базу и читаем ставки по ключам
    # rates[CCY] = CCY за 1 USD, т.е. USD->CCY = 1/rates[CCY], CCY->USD = rates[CCY]
    def _get(ccy: str) -> float:
        if ccy not in rates:
            raise ValueError(f"Не удалось получить курс для {ccy}->{base}")
        return float(rates[ccy])

    if from_code == base:
        # base -> to
        rate = 1.0 / _get(to_code)
    elif to_code == base:
        # from -> base
        rate = _get(from_code)
    else:
        # cross: from -> to через base
        rate = _get(from_code) / _get(to_code)

    return {
        "from": from_code,
        "to": to_code,
        "rate": rate,
        "source": data.get("source", "LocalCache"),
        "last_refresh": data.get("last_refresh"),
        "base": base,
    }



#Регистрация/логин/сессия

SESSION_JSON = data_file("session.json")


def _next_user_id(users: list[dict]) -> int:
    if not users:
        return 1
    return int(max(u.get("user_id", 0) for u in users)) + 1


def _find_user_by_username(users: list[dict], username: str) -> dict | None:
    for u in users:
        if u.get("username") == username:
            return u
    return None


def get_current_user() -> dict | None:
    #Текущий пользователь из session.json или None
    session = read_json(SESSION_JSON, default={"user_id": None, "username": None})
    if session.get("user_id") is None:
        return None
    return session


def logout() -> None:
    #Сброс сессии
    write_json(SESSION_JSON, {"user_id": None, "username": None})


def register(username: str, password: str) -> dict:
    # Регистрация пользователя
    name = validate_username(username)
    pwd = validate_password(password)

    users = load_users()
    if _find_user_by_username(users, name) is not None:
        raise ValueError("Пользователь с таким именем уже существует.")

    user_id = _next_user_id(users)
    user = User.create_new(user_id=user_id, username=name, password=pwd)
    users.append(user.to_dict())
    save_users(users)

    portfolios = load_portfolios()
    portfolio = Portfolio(user=user)
    portfolios.append(portfolio.to_dict())
    save_portfolios(portfolios)

    return user.get_user_info()


def login(username: str, password: str) -> dict:
    # Логин пользователя
    name = validate_username(username)
    pwd = str(password) if password is not None else ""

    users = load_users()
    raw = _find_user_by_username(users, name)
    if raw is None:
        raise ValueError("Неверное имя пользователя или пароль.")

    user = User(
        user_id=raw["user_id"],
        username=raw["username"],
        hashed_password=raw["hashed_password"],
        salt=raw["salt"],
        registration_date=raw["registration_date"],
    )

    if not user.verify_password(pwd):
        raise ValueError("Неверное имя пользователя или пароль.")

    write_json(SESSION_JSON, {"user_id": user.user_id, "username": user.username})
    return user.get_user_info()


def show_portfolio(base_currency: str = "USD") -> dict:
    # Показать портфель текущего пользователя
    session = get_current_user()
    if session is None:
        raise ValueError("Необходимо выполнить login.")

    user_id = session["user_id"]
    base = normalize_currency_code(base_currency)

    portfolios = load_portfolios()
    raw = None
    for p in portfolios:
        if p.get("user_id") == user_id:
            raw = p
            break
    if raw is None:
        raise ValueError("Портфель не найден.")

    # восстановим портфель в объектную модель
    users = load_users()
    u_raw = None
    for u in users:
        if u.get("user_id") == user_id:
            u_raw = u
            break
    if u_raw is None:
        raise ValueError("Пользователь не найден.")

    user = User(
        user_id=u_raw["user_id"],
        username=u_raw["username"],
        hashed_password=u_raw["hashed_password"],
        salt=u_raw["salt"],
        registration_date=u_raw["registration_date"],
    )

    wallets = {}
    raw_wallets = raw.get("wallets", {})
    for code, w in raw_wallets.items():
        # w: {"currency_code": "...", "balance": ...}
        wallets[code] = Wallet(currency_code=w["currency_code"], balance=w["balance"])

    portfolio = Portfolio(user=user, wallets=wallets)

    rows = []
    for w in portfolio.wallets.values():
        rows.append({"currency_code": w.currency_code, "balance": w.balance})

    total = portfolio.get_total_value(base_currency=base)

    return {
        "user": user.get_user_info(),
        "wallets": rows,
        "total_value": total,
        "base_currency": base,
    }


def _load_user_portfolio(user_id: int) -> dict:
    portfolios = load_portfolios()
    for p in portfolios:
        if p.get("user_id") == user_id:
            return p
    raise ValueError("Портфель не найден.")


def _save_user_portfolio(updated: dict) -> None:
    portfolios = load_portfolios()
    user_id = updated.get("user_id")
    out = []
    replaced = False
    for p in portfolios:
        if p.get("user_id") == user_id:
            out.append(updated)
            replaced = True
        else:
            out.append(p)
    if not replaced:
        out.append(updated)
    save_portfolios(out)


@log_action("buy")
def buy_currency(currency_code: str, amount: Any) -> dict:
    # Покупка валюты: увеличиваем баланс кошелька currency_code на amount
    session = get_current_user()
    if session is None:
        raise ValueError("Необходимо выполнить login.")

    cur = get_currency(currency_code)
    code = cur.code
    amt = validate_amount(amount)

    user_id = session["user_id"]
    portfolio = _load_user_portfolio(user_id)
    wallets = portfolio.get("wallets", {})

    if code not in wallets:
        wallets[code] = {"currency_code": code, "balance": 0.0}

    wallets[code]["balance"] = float(wallets[code]["balance"]) + float(amt)
    portfolio["wallets"] = wallets

    _save_user_portfolio(portfolio)
    return {"currency_code": code, "balance": wallets[code]["balance"]}


@log_action("sell")
def sell_currency(currency_code: str, amount: Any) -> dict:
    # Продажа валюты: уменьшаем баланс кошелька currency_code на amount
    session = get_current_user()
    if session is None:
        raise ValueError("Необходимо выполнить login.")

    # Валюта через реестр (если неизвестна - CurrencyNotFoundError)
    cur = get_currency(currency_code)
    code = cur.code

    amt = validate_amount(amount)

    user_id = session["user_id"]
    portfolio = _load_user_portfolio(user_id)
    wallets = portfolio.get("wallets", {})

    # Если кошелька нет - считаем доступно 0.0 и кидаем InsufficientFundsError
    if code not in wallets:
        raise InsufficientFundsError(available=0.0, required=float(amt), code=code)

    balance = float(wallets[code]["balance"])
    if float(amt) > balance:
        raise InsufficientFundsError(available=balance, required=float(amt), code=code)

    wallets[code]["balance"] = balance - float(amt)
    portfolio["wallets"] = wallets

    _save_user_portfolio(portfolio)
    return {"currency_code": code, "balance": wallets[code]["balance"]}

