import json
import unittest
from pathlib import Path

from valutatrade_hub.core.usecases import get_current_user, login, logout, register

DATA_FILES = [
    Path("data/users.json"),
    Path("data/portfolios.json"),
    Path("data/session.json"),
]


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


class TestAuth(unittest.TestCase):
    def setUp(self) -> None:
        # бэкап текущих data файлов
        self.backup = {}
        for p in DATA_FILES:
            if p.exists():
                self.backup[str(p)] = p.read_text(encoding="utf-8")

        _write(Path("data/users.json"), [])
        _write(Path("data/portfolios.json"), [])
        _write(Path("data/session.json"), {"user_id": None, "username": None})

    def tearDown(self) -> None:
        # восстановление
        for p in DATA_FILES:
            key = str(p)
            if key in self.backup:
                p.write_text(self.backup[key], encoding="utf-8")

    def test_register_and_login(self) -> None:
        info = register("alice", "1234")
        self.assertEqual(info["username"], "alice")

        # логин
        info2 = login("alice", "1234")
        self.assertEqual(info2["username"], "alice")

        sess = get_current_user()
        self.assertIsNotNone(sess)
        self.assertEqual(sess["username"], "alice")

        logout()
        self.assertIsNone(get_current_user())

    def test_register_duplicate(self) -> None:
        register("alice", "1234")
        with self.assertRaises(ValueError):
            register("alice", "9999")

    def test_login_wrong_password(self) -> None:
        register("alice", "1234")
        with self.assertRaises(ValueError):
            login("alice", "0000")


if __name__ == "__main__":
    unittest.main()
