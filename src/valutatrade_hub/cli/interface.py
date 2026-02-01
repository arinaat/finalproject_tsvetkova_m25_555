# Командный интерфейс

from __future__ import annotations

import argparse
import logging

from prettytable import PrettyTable

from valutatrade_hub.core.usecases import (
    buy_currency,
    get_current_user,
    get_rate,
    login,
    logout,
    register,
    sell_currency,
    show_portfolio,
)
from valutatrade_hub.infra.logging_config import setup_parser_service_logger
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.updater import RatesUpdater


def _print_portfolio(result: dict) -> None:
    table = PrettyTable()
    table.field_names = ["Валюта", "Баланс"]
    for row in result["wallets"]:
        table.add_row([row["currency_code"], row["balance"]])

    print(table)
    print(f"Итого в {result['base_currency']}: {result['total_value']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="valutatrade-hub")
    sub = parser.add_subparsers(dest="command", required=True)

    # register
    sp = sub.add_parser("register", help="Регистрация пользователя")
    sp.add_argument("username", help="Имя пользователя")
    sp.add_argument("password", help="Пароль (минимум 4 символа)")

    # login
    sp = sub.add_parser("login", help="Вход пользователя")
    sp.add_argument("username", help="Имя пользователя")
    sp.add_argument("password", help="Пароль")

    # logout
    sub.add_parser("logout", help="Выход (сброс сессии)")

    # get-rate
    sp = sub.add_parser("get-rate", help="Получить курс валют")
    sp.add_argument("from_currency", help="Из валюты (например, EUR)")
    sp.add_argument("to_currency", help="В валюту (например, USD)")

    # buy
    sp = sub.add_parser("buy", help="Купить валюту")
    sp.add_argument("currency_code", help="Код валюты (например, EUR)")
    sp.add_argument("amount", type=float, help="Сумма (> 0)")

    # sell
    sp = sub.add_parser("sell", help="Продать валюту")
    sp.add_argument("currency_code", help="Код валюты (например, EUR)")
    sp.add_argument("amount", type=float, help="Сумма (> 0)")

    # show-portfolio
    sp = sub.add_parser("show-portfolio", help="Показать портфель пользователя")
    sp.add_argument("--base", default="USD", help="Базовая валюта (USD по умолчанию)")

    # update-rates (parser_service)
    sp = sub.add_parser("update-rates", help="Обновить курсы (parser_service)")
    sp.add_argument(
        "--source",
        choices=["all", "coingecko", "exchangerate"],
        default="all",
        help="Источник курсов: all/coingecko/exchangerate",
    )

    sp = sub.add_parser(
        "show-rates",
        help="Показать курсы из локального кеша",
    )
    sp.add_argument(
        "--currency",
        help="Показать курс только для валюты (например, BTC)",
    )
    sp.add_argument(
        "--top",
        type=int,
        help="Показать N самых дорогих (по rate)",
    )
    sp.add_argument(
        "--base",
        default="USD",
        help="Базовая валюта для вывода (USD по умолчанию)",
    )

    return parser


def run_cli(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "show-rates":
        from prettytable import PrettyTable

        from valutatrade_hub.core.utils import read_json

        settings = SettingsLoader().load()
        data = read_json(settings.rates_json, default={})
        pairs = data.get("pairs_usd_per_unit") or data.get("pairs") or {}
        last_refresh = data.get("last_refresh")
        source = data.get("source")

        rows = []
        for k, v in pairs.items():
            if isinstance(v, dict) and "rate" in v:
                rate = v.get("rate")
                updated = v.get("updated_at") or v.get("timestamp") or last_refresh
                src = v.get("source") or source
            else:
                rate = v
                updated = last_refresh
                src = source

            if isinstance(k, str) and "_" in k:
                frm, to = k.split("_", 1)
            else:
                frm, to = str(k), args.base

            rows.append((frm, to, rate, updated, src))

        if args.currency:
            cur = args.currency.upper()
            rows = [r for r in rows if r[0].upper() == cur]

        def to_float(x):
            try:
                return float(x)
            except Exception:
                return None

        if args.top:
            rows = sorted(
                rows,
                key=lambda r: (to_float(r[2]) is None, to_float(r[2]) or 0.0),
                reverse=True,
            )[: args.top]

        t = PrettyTable()
        t.field_names = ["from", "to", "rate", "updated_at", "source"]
        for frm, to, rate, updated, src in rows:
            t.add_row([frm, to, rate, updated, src])
        print(t)
        return

    settings = SettingsLoader().load()
    setup_parser_service_logger(settings.logs_dir / "parser_service.log")

    try:
        if args.command == "register":
            info = register(args.username, args.password)
            msg = (
                f"Пользователь зарегистрирован: {info['username']} "
                f"(id={info['user_id']})"
            )
            print(msg)
            return

        if args.command == "login":
            info = login(args.username, args.password)
            print(f"Успешный вход: {info['username']}")
            return

        if args.command == "logout":
            logout()
            print("Вы вышли из аккаунта.")
            return

        if args.command == "get-rate":
            r = get_rate(args.from_currency, args.to_currency)
            msg = (
                f"Курс {r['from']} -> {r['to']}: {r['rate']} "
                f"(источник: {r['source']}, обновлено: {r['last_refresh']})"
            )
            print(msg)
            return

        if args.command == "buy":
            if get_current_user() is None:
                raise ValueError("Сначала выполните login.")
            res = buy_currency(args.currency_code, args.amount)
            print(f"Покупка выполнена: {res['currency_code']} баланс={res['balance']}")
            return

        if args.command == "sell":
            if get_current_user() is None:
                raise ValueError("Сначала выполните login.")
            res = sell_currency(args.currency_code, args.amount)
            print(f"Продажа выполнена: {res['currency_code']} баланс={res['balance']}")
            return

        if args.command == "show-portfolio":
            if get_current_user() is None:
                raise ValueError("Сначала выполните login.")
            result = show_portfolio(base_currency=args.base)
            _print_portfolio(result)
            return

        if args.command == "update-rates":
            cfg = ParserConfig.from_env()
            clients = [CoinGeckoClient(cfg), ExchangeRateApiClient(cfg)]
            updater = RatesUpdater(cfg, clients)
            res = updater.run_update()
            updated = res.get("updated_pairs", 0)
            errors = res.get("errors", [])
            print(f"Курсы обновлены. Пар: {updated}. Ошибок: {len(errors)}")
            return

        raise ValueError("Неизвестная команда.")

    except ValueError as e:
        raise SystemExit(f"Ошибка: {e}") from e
    except Exception as e:
        logging.getLogger("parser_service").exception("CLI: внутренняя ошибка")
        msg = "Ошибка: Внутренняя ошибка. Подробности в logs/parser_service.log"
        raise SystemExit(msg) from e
