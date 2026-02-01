#Точка входа консольного приложения

from __future__ import annotations

import sys

from valutatrade_hub.cli.interface import run_cli


def main() -> None:
    run_cli(sys.argv[1:])


if __name__ == "__main__":
    main()
