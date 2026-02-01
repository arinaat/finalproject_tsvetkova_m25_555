#Бизнес-логика

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from valutatrade_hub.core.models import Portfolio, User
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
    validate_password,
    validate_username,
    write_json,
)

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


def _is_fresh(last_refresh: Any, ttl_seconds: int = CACHE_TTL_SECONDS) -> bool:
    dt = _parse_iso_dt(last_refresh)
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

    Курсы:
    - base=USD
    - rates[CCY] = сколько CCY за 1 USD
    """
    frm = normalize_currency_code(from_currency)
    to = normalize_currency_code(to_currency)

    data = ensure_rates_fresh()
    base = normalize_currency_code(data.get("base", "USD"))
    rates: dict[str, float] = data.get("rates", {})

    if frm == to:
        rate = 1.0
    else:
        if base not in rates:
            rates[base] = 1.0

        if frm not in rates or to not in rates:
            raise ValueError("Курс для указанной валюты недоступен.")

        def to_usd(x: str) -> float:
            if x == base:
                return 1.0
            return 1.0 / float(rates[x])

        def from_usd(x: str) -> float:
            if x == base:
                return 1.0
            return float(rates[x])

        rate = to_usd(frm) * from_usd(to)

    return {
        "from": frm,
        "to": to,
        "rate": float(rate),
        "source": data.get("source"),
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
