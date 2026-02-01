import unittest

from valutatrade_hub.infra.decorators import log_action
from valutatrade_hub.infra.settings import SettingsLoader


class TestLoggingDecorator(unittest.TestCase):
    def test_log_file_written(self) -> None:
        settings = SettingsLoader().reload()
        # очистим лог перед тестом
        if settings.actions_log.exists():
            settings.actions_log.unlink()

        @log_action("test_action")
        def f(x: int) -> int:
            return x + 1

        self.assertEqual(f(1), 2)

        self.assertTrue(settings.actions_log.exists())
        txt = settings.actions_log.read_text(encoding="utf-8")
        self.assertIn("START test_action", txt)
        self.assertIn("OK test_action", txt)


if __name__ == "__main__":
    unittest.main()
