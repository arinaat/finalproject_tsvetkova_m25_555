# Настройка логирования проекта

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

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
