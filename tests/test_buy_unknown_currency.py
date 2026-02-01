import unittest

from valutatrade_hub.core.exceptions import CurrencyNotFoundError
from valutatrade_hub.core.usecases import buy_currency, login, register


class TestBuyUnknownCurrency(unittest.TestCase):
    def setUp(self) -> None:
        try:
            register("alice", "1234")
        except Exception:
            pass
        login("alice", "1234")

    def test_buy_unknown_currency_raises(self) -> None:
        with self.assertRaises(CurrencyNotFoundError):
            buy_currency("ZZZ", 10)


if __name__ == "__main__":
    unittest.main()
