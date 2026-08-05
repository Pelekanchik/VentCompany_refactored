"""
Репозиторій для роботи з матеріалами
"""
import sqlite3
from typing import List, Dict, Any, Optional
from ventilation_company.database import get_calc_db


class MaterialRepo:
    """CRUD для calc_materials, subtype_materials"""

    # ── calc_materials ──
    @staticmethod
    def get_all_materials() -> List[sqlite3.Row]:
        db = get_calc_db()
        rows = db.execute("SELECT * FROM calc_materials ORDER BY name, thickness").fetchall()
        db.close()
        return rows

    @staticmethod
    def get_material_by_id(material_id: int) -> Optional[sqlite3.Row]:
        db = get_calc_db()
        row = db.execute("SELECT * FROM calc_materials WHERE id=?", (material_id,)).fetchone()
        db.close()
        return row

    @staticmethod
    def get_materials_by_subtype(subtype_id: int) -> List[sqlite3.Row]:
        db = get_calc_db()
        rows = db.execute(
            """SELECT m.*, sm.is_default
               FROM calc_materials m
               JOIN subtype_materials sm ON m.id = sm.material_id
               WHERE sm.subtype_id=?""",
            (subtype_id,)
        ).fetchall()
        db.close()
        return rows

    @staticmethod
    def add_material(name: str, grade: str, thickness: float,
                     unit: str = "мм", price_per_kg: float = 0.0,
                     density: float = 0.0) -> int:
        db = get_calc_db()
        cursor = db.execute(
            """INSERT INTO calc_materials
               (name, grade, thickness, unit, price_per_kg, density)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, grade, thickness, unit, price_per_kg, density)
        )
        db.commit()
        last_id = cursor.lastrowid
        db.close()
        return last_id

    @staticmethod
    def update_material(material_id: int, **kwargs) -> None:
        db = get_calc_db()
        allowed = {"name", "grade", "thickness", "unit", "price_per_kg", "density"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            db.close()
            return
        set_clause = ", ".join(f"{k}=?" for k in fields)
        values = list(fields.values()) + [material_id]
        db.execute(f"UPDATE calc_materials SET {set_clause} WHERE id=?", values)
        db.commit()
        db.close()

    @staticmethod
    def delete_material(material_id: int) -> None:
        db = get_calc_db()
        db.execute("DELETE FROM calc_materials WHERE id=?", (material_id,))
        db.commit()
        db.close()

    # ── subtype_materials ──
    @staticmethod
    def link_material_to_subtype(subtype_id: int, material_id: int, is_default: bool = False) -> None:
        db = get_calc_db()
        db.execute(
            """INSERT OR REPLACE INTO subtype_materials
               (subtype_id, material_id, is_default)
               VALUES (?, ?, ?)""",
            (subtype_id, material_id, int(is_default))
        )
        db.commit()
        db.close()

    @staticmethod
    def unlink_material_from_subtype(subtype_id: int, material_id: int) -> None:
        db = get_calc_db()
        db.execute(
            "DELETE FROM subtype_materials WHERE subtype_id=? AND material_id=?",
            (subtype_id, material_id)
        )
        db.commit()
        db.close()

    @staticmethod
    def set_default_material(subtype_id: int, material_id: int) -> None:
        db = get_calc_db()
        db.execute(
            "UPDATE subtype_materials SET is_default=0 WHERE subtype_id=?",
            (subtype_id,)
        )
        db.execute(
            "UPDATE subtype_materials SET is_default=1 WHERE subtype_id=? AND material_id=?",
            (subtype_id, material_id)
        )
        db.commit()
        db.close()

    @staticmethod
    def get_material_full(material_id: int):
        db = get_calc_db()
        row = db.execute("SELECT * FROM calc_materials WHERE id=?", (material_id,)).fetchone()
        db.close()
        return row

    @staticmethod
    def update_material_full(material_id: int, name: str, grade: str,
                               thickness: float, unit: str = "мм",
                               price_per_kg: float = 0.0, density: float = 0.0) -> None:
        db = get_calc_db()
        db.execute(
            """UPDATE calc_materials SET
                name=?, grade=?, thickness=?, unit=?, price_per_kg=?, density=?
                WHERE id=?""",
            (name, grade, thickness, unit, price_per_kg, density, material_id)
        )
        db.commit()
        db.close()

    @staticmethod
    def clear_subtype_materials(subtype_id: int) -> None:
        db = get_calc_db()
        db.execute("DELETE FROM subtype_materials WHERE subtype_id=?", (subtype_id,))
        db.commit()
        db.close()

