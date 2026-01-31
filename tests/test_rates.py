import unittest

from valutatrade_hub.core.usecases import ensure_rates_fresh, get_rate


class TestRates(unittest.TestCase):
    def test_ensure_rates_fresh(self) -> None:
        data = ensure_rates_fresh()
        self.assertIn("rates", data)
        self.assertIn("last_refresh", data)
        self.assertIn("base", data)

    def test_get_rate_identity(self) -> None:
        r = get_rate("usd", "USD")
        self.assertEqual(r["rate"], 1.0)

    def test_get_rate_cross(self) -> None:
        r = get_rate("EUR", "RUB")
        self.assertGreater(r["rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
