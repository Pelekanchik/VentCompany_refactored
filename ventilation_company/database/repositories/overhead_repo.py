"""
Репозиторій для роботи з накладними витратами
"""
import sqlite3
from typing import List, Dict, Any, Optional
from ventilation_company.database import get_calc_db


class OverheadRepo:
    """CRUD для overhead_items"""

    @staticmethod
    def get_all() -> List[sqlite3.Row]:
        db = get_calc_db()
        rows = db.execute(
            "SELECT * FROM overhead_items WHERE is_active=1 ORDER BY name"
        ).fetchall()
        db.close()
        return rows

    @staticmethod
    def get_by_id(item_id: int) -> Optional[sqlite3.Row]:
        db = get_calc_db()
        row = db.execute(
            "SELECT * FROM overhead_items WHERE id=?", (item_id,)
        ).fetchone()
        db.close()
        return row

    @staticmethod
    def add(name: str, item_type: str = "fixed", value: float = 0.0) -> int:
        db = get_calc_db()
        cursor = db.execute(
            "INSERT INTO overhead_items (name, type, value, is_active) VALUES (?, ?, ?, 1)",
            (name, item_type, value)
        )
        db.commit()
        last_id = cursor.lastrowid
        db.close()
        return last_id

    @staticmethod
    def update(item_id: int, **kwargs) -> None:
        db = get_calc_db()
        allowed = {"name", "type", "value", "is_active"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            db.close()
            return
        set_clause = ", ".join(f"{k}=?" for k in fields)
        values = list(fields.values()) + [item_id]
        db.execute(f"UPDATE overhead_items SET {set_clause} WHERE id=?", values)
        db.commit()
        db.close()

    @staticmethod
    def delete(item_id: int) -> None:
        db = get_calc_db()
        db.execute("UPDATE overhead_items SET is_active=0 WHERE id=?", (item_id,))
        db.commit()
        db.close()

    @staticmethod
    def get_total_overhead() -> float:
        db = get_calc_db()
        row = db.execute(
            "SELECT SUM(value) as total FROM overhead_items WHERE is_active=1"
        ).fetchone()
        db.close()
        return row["total"] or 0.0

    @staticmethod
    def get_overhead_full(item_id: int):
        db = get_calc_db()
        row = db.execute("SELECT * FROM overhead_items WHERE id=?", (item_id,)).fetchone()
        db.close()
        return row

    @staticmethod
    def update_overhead_full(item_id: int, name: str, item_type: str, value: float) -> None:
        db = get_calc_db()
        db.execute(
            "UPDATE overhead_items SET name=?, type=?, value=? WHERE id=?",
            (name, item_type, value, item_id)
        )
        db.commit()
        db.close()

    @staticmethod
    def add_overhead_full(name: str, item_type: str, value: float) -> int:
        db = get_calc_db()
        cursor = db.execute(
            "INSERT INTO overhead_items (name, type, value, is_active) VALUES (?, ?, ?, 1)",
            (name, item_type, value)
        )
        db.commit()
        last_id = cursor.lastrowid
        db.close()
        return last_id

