import unittest
from pathlib import Path

from valutatrade_hub.core.usecases import login, register, show_portfolio
from valutatrade_hub.core.utils import write_json


def _write(path: Path, obj):
    write_json(path, obj)


class TestShowPortfolio(unittest.TestCase):
    def setUp(self) -> None:
        # чистим data
        _write(Path("data/users.json"), [])
        _write(Path("data/portfolios.json"), [])
        _write(Path("data/session.json"), {"user_id": None, "username": None})

    def test_show_portfolio_empty(self) -> None:
        register("alice", "1234")
        login("alice", "1234")

        res = show_portfolio("USD")
        self.assertEqual(res["user"]["username"], "alice")
        self.assertEqual(res["wallets"], [])
        self.assertIsInstance(res["total_value"], float)


if __name__ == "__main__":
    unittest.main()
