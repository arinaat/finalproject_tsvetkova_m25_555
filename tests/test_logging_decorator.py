import logging
import unittest
from io import StringIO
from unittest.mock import patch

from valutatrade_hub.infra.decorators import log_action


class TestLoggingDecorator(unittest.TestCase):
    def test_log_messages_written(self) -> None:
        buf = StringIO()

        logger = logging.getLogger("test_actions_logger")
        logger.setLevel(logging.INFO)

        # Сбрасываем хендлеры, чтобы тест был детерминированным
        logger.handlers = []
        handler = logging.StreamHandler(buf)
        handler.setLevel(logging.INFO)

        # Важно: формат без времени, чтобы просто проверять текст
        handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.propagate = False

        # Патчим именно функцию, которую decorators.py импортировал
        with patch(
            "valutatrade_hub.infra.decorators.get_actions_logger",
            return_value=logger,
        ):

            @log_action("test")
            def dummy() -> int:
                return 1

            res = dummy()
            self.assertEqual(res, 1)

        text = buf.getvalue()
        self.assertIn("INFO START test", text)
        self.assertIn("INFO OK test", text)


if __name__ == "__main__":
    unittest.main()
