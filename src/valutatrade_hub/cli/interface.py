# Командный интерфейс

from __future__ import annotations

import argparse

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

    return parser


def run_cli(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = SettingsLoader()
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

        raise ValueError("Неизвестная команда.")
    except ValueError as e:
        raise SystemExit(f"Ошибка: {e}")
    except Exception:
        raise SystemExit("Ошибка: Внутренняя ошибка.")
