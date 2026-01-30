import unittest
from datetime import datetime

from valutatrade_hub.core.models import Portfolio, User, Wallet


class TestModels(unittest.TestCase):
    def test_user_password_flow(self) -> None:
        reg_dt = datetime(2025, 10, 9, 12, 0, 0)
        user = User.create_new(
            user_id=1,
            username="alice",
            password="1234",
            registration_date=reg_dt,
        )

        self.assertTrue(user.verify_password("1234"))
        self.assertFalse(user.verify_password("0000"))

        user.change_password("abcd")
        self.assertTrue(user.verify_password("abcd"))
        self.assertFalse(user.verify_password("1234"))

        info = user.get_user_info()
        self.assertIn("user_id", info)
        self.assertIn("username", info)
        self.assertIn("registration_date", info)
        self.assertNotIn("hashed_password", info)

    def test_user_username_validation(self) -> None:
        with self.assertRaises(ValueError):
            User.create_new(user_id=1, username="   ", password="1234")

    def test_wallet_balance_rules(self) -> None:
        w = Wallet("usd", 0.0)
        w.deposit(10)
        self.assertEqual(w.balance, 10.0)

        w.withdraw(3)
        self.assertEqual(w.balance, 7.0)

        with self.assertRaises(ValueError):
            w.withdraw(100)

        with self.assertRaises(ValueError):
            w.deposit(-1)

        with self.assertRaises(ValueError):
            w.balance = -5

    def test_portfolio_total_value(self) -> None:
        user = User.create_new(user_id=1, username="alice", password="1234")
        p = Portfolio(user=user)

        p.add_currency("USD").deposit(150)
        p.add_currency("BTC").deposit(0.05)

        total = p.get_total_value(base_currency="USD")
        self.assertGreater(total, 150.0)

        with self.assertRaises(ValueError):
            p.add_currency("USD")


if __name__ == "__main__":
    unittest.main()
