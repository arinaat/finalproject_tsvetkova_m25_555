import unittest

from valutatrade_hub.infra.settings import SettingsLoader


class TestSettingsSingleton(unittest.TestCase):
    def test_singleton_identity(self) -> None:
        a = SettingsLoader()
        b = SettingsLoader()
        self.assertIs(a, b)

    def test_defaults_exist(self) -> None:
        s = SettingsLoader().load()
        self.assertEqual(s.default_base_currency, "USD")
        self.assertGreater(s.rates_ttl_seconds, 0)


if __name__ == "__main__":
    unittest.main()
