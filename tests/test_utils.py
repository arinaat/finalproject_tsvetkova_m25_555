import unittest
from pathlib import Path

from valutatrade_hub.core.utils import (
    normalize_currency_code,
    read_json,
    validate_amount,
    validate_password,
    validate_username,
    write_json,
)


class TestUtils(unittest.TestCase):
    def test_normalize_currency_code(self) -> None:
        self.assertEqual(normalize_currency_code(" usd "), "USD")
        with self.assertRaises(ValueError):
            normalize_currency_code("   ")

    def test_validate_username(self) -> None:
        self.assertEqual(validate_username(" alice "), "alice")
        with self.assertRaises(ValueError):
            validate_username("   ")

    def test_validate_password(self) -> None:
        self.assertEqual(validate_password("1234"), "1234")
        with self.assertRaises(ValueError):
            validate_password("123")

    def test_validate_amount(self) -> None:
        self.assertEqual(validate_amount(1), 1.0)
        self.assertEqual(validate_amount(2.5), 2.5)
        with self.assertRaises(ValueError):
            validate_amount(0)
        with self.assertRaises(ValueError):
            validate_amount(-1)

    def test_read_write_json(self) -> None:
        tmp = Path("data/_tmp_test.json")
        write_json(tmp, {"a": 1})
        self.assertEqual(read_json(tmp, default={}), {"a": 1})
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
