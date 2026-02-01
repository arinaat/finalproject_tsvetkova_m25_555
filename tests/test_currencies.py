import unittest

from valutatrade_hub.core.currencies import CryptoCurrency, FiatCurrency, get_currency
from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class TestCurrencies(unittest.TestCase):
    def test_get_currency_ok(self) -> None:
        usd = get_currency("usd")
        self.assertEqual(usd.code, "USD")
        self.assertIn("USD", usd.get_display_info())

    def test_get_currency_unknown(self) -> None:
        with self.assertRaises(CurrencyNotFoundError):
            get_currency("ZZZ")

    def test_display_info_formats(self) -> None:
        fiat = FiatCurrency(name="Test", code="AAA", issuing_country="Nowhere")
        self.assertTrue(fiat.get_display_info().startswith("[FIAT]"))

        crypto = CryptoCurrency(
            name="Coin", code="COIN", algorithm="Algo", market_cap=1.0
        )
        self.assertTrue(crypto.get_display_info().startswith("[CRYPTO]"))


if __name__ == "__main__":
    unittest.main()
