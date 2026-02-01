# Командный интерфейс

from __future__ import annotations

import argparse

from prettytable import PrettyTable

from valutatrade_hub.core.usecases import (
    get_current_user,
    get_rate,
    login,
    logout,
    register,
    show_portfolio,
)


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

    # show-portfolio
    sp = sub.add_parser("show-portfolio", help="Показать портфель пользователя")
    sp.add_argument("--base", default="USD", help="Базовая валюта (USD по умолчанию)")

    return parser


def run_cli(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

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
            print(
                f"Курс {r['from']} -> {r['to']}: {r['rate']} "
                f"(источник: {r['source']}, обновлено: {r['last_refresh']})"
            )
            return

        if args.command == "show-portfolio":
            user = get_current_user()
            if user is None:
                raise ValueError("Сначала выполните login.")
            result = show_portfolio(base_currency=args.base)
            _print_portfolio(result)
            return

        raise ValueError("Неизвестная команда.")
    except ValueError as e:
        raise SystemExit(f"Ошибка: {e}") from e
