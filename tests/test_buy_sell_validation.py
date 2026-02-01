import unittest
from pathlib import Path

from valutatrade_hub.core.usecases import buy_currency, login, register, sell_currency
from valutatrade_hub.core.utils import write_json


class TestBuySellValidation(unittest.TestCase):
    def setUp(self) -> None:
        write_json(Path("data/users.json"), [])
        write_json(Path("data/portfolios.json"), [])
        write_json(Path("data/session.json"), {"user_id": None, "username": None})
        register("alice", "1234")
        login("alice", "1234")

    def test_amount_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            buy_currency("EUR", 0)
        with self.assertRaises(ValueError):
            buy_currency("EUR", -1)

        buy_currency("EUR", 1)

        with self.assertRaises(ValueError):
            sell_currency("EUR", 0)
        with self.assertRaises(ValueError):
            sell_currency("EUR", -2)


if __name__ == "__main__":
    unittest.main()
