#Командный интерфейс

from __future__ import annotations

import argparse

from prettytable import PrettyTable

from valutatrade_hub.core.usecases import get_current_user, show_portfolio


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

    sp = sub.add_parser("show-portfolio", help="Показать портфель пользователя")
    sp.add_argument("--base", default="USD", help="Базовая валюта (USD по умолчанию)")
    return parser


def run_cli(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "show-portfolio":
        user = get_current_user()
        if user is None:
            raise SystemExit("Ошибка: сначала выполните login.")
        result = show_portfolio(base_currency=args.base)
        _print_portfolio(result)
