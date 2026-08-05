"""
Репозиторій для роботи з налаштуваннями калькулятора
"""

from typing import Any

from ventilation_company.database import get_calc_db


class SettingsRepo:
    """CRUD для calc_settings"""

    @staticmethod
    def get(key: str, default: str = "") -> str:
        db = get_calc_db()
        row = db.execute("SELECT value FROM calc_settings WHERE key=?", (key,)).fetchone()
        db.close()
        return row["value"] if row else default

    @staticmethod
    def get_float(key: str, default: float = 0.0) -> float:
        val = SettingsRepo.get(key)
        try:
            return float(val) if val else default
        except ValueError:
            return default

    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        val = SettingsRepo.get(key)
        try:
            return int(val) if val else default
        except ValueError:
            return default

    @staticmethod
    def set(key: str, value: Any) -> None:
        db = get_calc_db()
        db.execute(
            """INSERT INTO calc_settings (key, value)
               VALUES (?, ?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
            (key, str(value)),
        )
        db.commit()
        db.close()

    @staticmethod
    def get_all() -> dict[str, str]:
        db = get_calc_db()
        rows = db.execute("SELECT key, value FROM calc_settings").fetchall()
        db.close()
        return {r["key"]: r["value"] for r in rows}

    @staticmethod
    def delete(key: str) -> None:
        db = get_calc_db()
        db.execute("DELETE FROM calc_settings WHERE key=?", (key,))
        db.commit()
        db.close()

    @staticmethod
    def get_dict(key: str, default: dict = None) -> dict:
        import json

        val = SettingsRepo.get(key)
        if val:
            try:
                return json.loads(val)
            except Exception:
                pass
        return default or {}

    @staticmethod
    def set_dict(key: str, value: dict) -> None:
        import json

        SettingsRepo.set(key, json.dumps(value))
