# Настройка логирования проекта

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from valutatrade_hub.infra.settings import SettingsLoader


def get_actions_logger() -> logging.Logger:
    logger = logging.getLogger("valutatrade_hub.actions")
    if logger.handlers:
        return logger

    settings = SettingsLoader().load()
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        filename=str(settings.actions_log),
        maxBytes=512_000,
        backupCount=3,
        encoding="utf-8",
    )
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(fmt)

    logger.setLevel(getattr(logging, settings.log_level, logging.INFO))
    logger.addHandler(handler)
    logger.propagate = False
    return logger
    logger.propagate = False
    return logger



def setup_parser_service_logger(log_path: Path | None = None) -> Path:
    """Настраивает логгер parser_service в файл (сообщения на русском).

    - По умолчанию пишет в logs/parser_service.log (из SettingsLoader).
    - Не плодит хендлеры при повторных вызовах.
    """
    logger = logging.getLogger("parser_service")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        # Уже настроен
        base = getattr(logger.handlers[0], "baseFilename", "logs/parser_service.log")
        return Path(base)

    if log_path is None:
        settings = SettingsLoader().load()
        log_path = settings.logs_dir / "parser_service.log"

    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        filename=str(log_path),
        maxBytes=512_000,
        backupCount=3,
        encoding="utf-8",
    )
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(fmt)

    logger.addHandler(handler)
    logger.propagate = False
    return log_path
