# Декораторы проекта

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from valutatrade_hub.infra.logging_config import get_actions_logger

F = TypeVar("F", bound=Callable[..., Any])


def log_action(action_name: str) -> Callable[[F], F]:
    # Логирует начало/успех/ошибку действия

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_actions_logger()
            logger.info("START %s", action_name)
            try:
                result = func(*args, **kwargs)
                logger.info("OK %s", action_name)
                return result
            except Exception as e:
                logger.exception("ERROR %s: %s", action_name, e)
                raise

        return wrapper  # type: ignore[return-value]

    return decorator
