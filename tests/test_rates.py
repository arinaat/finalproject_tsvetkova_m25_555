import unittest

from valutatrade_hub.core.usecases import ensure_rates_fresh, get_rate


class TestRates(unittest.TestCase):
    def test_ensure_rates_fresh(self) -> None:
        data = ensure_rates_fresh()
        self.assertIn("rates", data)
        self.assertIn("base", data)
        self.assertIsInstance(data["rates"], dict)

    def test_get_rate_identity(self) -> None:
        r = get_rate("usd", "USD")
        self.assertEqual(r["rate"], 1.0)

    def test_get_rate_cross(self) -> None:
        data = ensure_rates_fresh()
        base = data.get("base", "USD")
        rates = data.get("rates") or {}

        # expected по формату: rates[X] = X за 1 base
        def per_base(code: str) -> float:
            if code == base:
                return 1.0
            return float(rates[code])

        expected = per_base("RUB") / per_base("EUR")
        r = get_rate("EUR", "RUB")
        self.assertAlmostEqual(r["rate"], expected, places=10)

    def test_unknown_currency_raises(self) -> None:
        with self.assertRaises(ValueError):
            get_rate("!!", "USD")


if __name__ == "__main__":
    unittest.main()
