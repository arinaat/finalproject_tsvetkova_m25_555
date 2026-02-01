import unittest

from valutatrade_hub.core.utils import validate_username


class TestUsernameLength(unittest.TestCase):
    def test_username_too_long(self) -> None:
        long_name = "a" * 500
        with self.assertRaises(ValueError):
            validate_username(long_name)


if __name__ == "__main__":
    unittest.main()
