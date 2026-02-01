# Пользовательские исключения проекта


class InsufficientFundsError(ValueError):
    # Недостаточно средств для операции

    def __init__(self, available: float, required: float, code: str) -> None:
        msg = (
            f"Недостаточно средств: доступно {available} {code}, "
            f"требуется {required} {code}"
        )
        super().__init__(msg)


class CurrencyNotFoundError(ValueError):
    # Неизвестная валюта

    def __init__(self, code: str) -> None:
        super().__init__(f"Неизвестная валюта '{code}'")


class ApiRequestError(RuntimeError):
    # Ошибка получения курсов/внешнего API

    def __init__(self, reason: str) -> None:
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
