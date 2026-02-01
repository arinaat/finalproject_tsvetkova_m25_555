import unittest
from pathlib import Path

from valutatrade_hub.core.usecases import buy_currency, login, register, sell_currency
from valutatrade_hub.core.utils import write_json


class TestBuySell(unittest.TestCase):
    def setUp(self) -> None:
        write_json(Path("data/users.json"), [])
        write_json(Path("data/portfolios.json"), [])
        write_json(Path("data/session.json"), {"user_id": None, "username": None})

        register("alice", "1234")
        login("alice", "1234")

    def test_buy_and_sell(self) -> None:
        r1 = buy_currency("eur", 10)
        self.assertEqual(r1["currency_code"], "EUR")
        self.assertEqual(r1["balance"], 10.0)

        r2 = sell_currency("EUR", 3)
        self.assertEqual(r2["balance"], 7.0)

        with self.assertRaises(ValueError):
            sell_currency("EUR", 100)


if __name__ == "__main__":
    unittest.main()
