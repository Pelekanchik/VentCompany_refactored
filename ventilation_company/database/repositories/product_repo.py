"""
Репозиторій для роботи з типами виробів, підтипами та розмірами
"""

import sqlite3

from ventilation_company.database import get_calc_db


class ProductRepo:
    """CRUD для product_types, product_subtypes, size_ranges"""

    # ── product_types ──
    @staticmethod
    def get_all_types() -> list[sqlite3.Row]:
        db = get_calc_db()
        rows = db.execute("SELECT * FROM product_types ORDER BY name").fetchall()
        db.close()
        return rows

    @staticmethod
    def get_type_by_id(type_id: int) -> sqlite3.Row | None:
        db = get_calc_db()
        row = db.execute("SELECT * FROM product_types WHERE id=?", (type_id,)).fetchone()
        db.close()
        return row

    @staticmethod
    def add_type(name: str, slug: str) -> int:
        db = get_calc_db()
        cursor = db.execute("INSERT INTO product_types (name, slug) VALUES (?, ?)", (name, slug))
        db.commit()
        last_id = cursor.lastrowid
        db.close()
        return last_id

    @staticmethod
    def update_type(type_id: int, name: str, slug: str) -> None:
        db = get_calc_db()
        db.execute("UPDATE product_types SET name=?, slug=? WHERE id=?", (name, slug, type_id))
        db.commit()
        db.close()

    @staticmethod
    def delete_type(type_id: int) -> None:
        db = get_calc_db()
        db.execute("DELETE FROM product_types WHERE id=?", (type_id,))
        db.commit()
        db.close()

    # ── product_subtypes ──
    @staticmethod
    def get_subtypes_by_type(type_id: int) -> list[sqlite3.Row]:
        db = get_calc_db()
        rows = db.execute(
            "SELECT * FROM product_subtypes WHERE product_type_id=? ORDER BY name", (type_id,)
        ).fetchall()
        db.close()
        return rows

    @staticmethod
    def get_subtype_by_id(subtype_id: int) -> sqlite3.Row | None:
        db = get_calc_db()
        row = db.execute("SELECT * FROM product_subtypes WHERE id=?", (subtype_id,)).fetchone()
        db.close()
        return row

    @staticmethod
    def add_subtype(
        type_id: int,
        name: str,
        slug: str,
        formula: str,
        has_flange: bool = False,
        labor_norm: float = 0.0,
        waste_factor: float = 1.0,
        shape: str = "rect",
        description: str = "",
    ) -> int:
        db = get_calc_db()
        cursor = db.execute(
            """INSERT INTO product_subtypes
               (product_type_id, name, slug, formula, has_flange,
                labor_norm, waste_factor, shape, description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                type_id,
                name,
                slug,
                formula,
                int(has_flange),
                labor_norm,
                waste_factor,
                shape,
                description,
            ),
        )
        db.commit()
        last_id = cursor.lastrowid
        db.close()
        return last_id

    @staticmethod
    def update_subtype(subtype_id: int, **kwargs) -> None:
        db = get_calc_db()
        allowed = {
            "name",
            "slug",
            "formula",
            "has_flange",
            "labor_norm",
            "waste_factor",
            "shape",
            "description",
        }
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            db.close()
            return
        set_clause = ", ".join(f"{k}=?" for k in fields)
        values = list(fields.values()) + [subtype_id]
        db.execute(f"UPDATE product_subtypes SET {set_clause} WHERE id=?", values)
        db.commit()
        db.close()

    @staticmethod
    def delete_subtype(subtype_id: int) -> None:
        db = get_calc_db()
        db.execute("DELETE FROM product_subtypes WHERE id=?", (subtype_id,))
        db.commit()
        db.close()

    # ── size_ranges ──
    @staticmethod
    def get_sizes_by_subtype(subtype_id: int) -> list[sqlite3.Row]:
        db = get_calc_db()
        rows = db.execute(
            "SELECT * FROM size_ranges WHERE subtype_id=? ORDER BY param_name", (subtype_id,)
        ).fetchall()
        db.close()
        return rows

    @staticmethod
    def get_size_labels(subtype_id: int) -> dict[str, str]:
        db = get_calc_db()
        rows = db.execute(
            "SELECT param_name, param_label FROM size_ranges WHERE subtype_id=?", (subtype_id,)
        ).fetchall()
        db.close()
        return {r["param_name"]: r["param_label"] for r in rows}

    @staticmethod
    def add_size(
        subtype_id: int,
        param_name: str,
        param_label: str,
        min_value: float = None,
        max_value: float = None,
        step: float = None,
        default_value: float = None,
    ) -> int:
        db = get_calc_db()
        cursor = db.execute(
            """INSERT INTO size_ranges
               (subtype_id, param_name, param_label, min_value, max_value, step, default_value)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (subtype_id, param_name, param_label, min_value, max_value, step, default_value),
        )
        db.commit()
        last_id = cursor.lastrowid
        db.close()
        return last_id

    @staticmethod
    def update_size(size_id: int, **kwargs) -> None:
        db = get_calc_db()
        allowed = {"param_name", "param_label", "min_value", "max_value", "step", "default_value"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            db.close()
            return
        set_clause = ", ".join(f"{k}=?" for k in fields)
        values = list(fields.values()) + [size_id]
        db.execute(f"UPDATE size_ranges SET {set_clause} WHERE id=?", values)
        db.commit()
        db.close()

    @staticmethod
    def delete_size(size_id: int) -> None:
        db = get_calc_db()
        db.execute("DELETE FROM size_ranges WHERE id=?", (size_id,))
        db.commit()
        db.close()

    @staticmethod
    def get_all_subtypes() -> list[sqlite3.Row]:
        db = get_calc_db()
        rows = db.execute("SELECT * FROM product_subtypes WHERE is_active=1").fetchall()
        db.close()
        return rows

    @staticmethod
    def add_type_with_sort(name: str, slug: str, sort_order: int = 0, icon: str = "") -> int:
        db = get_calc_db()
        cursor = db.execute(
            "INSERT INTO product_types (name, slug, sort_order, icon, is_active) VALUES (?, ?, ?, ?, 1)",
            (name, slug, sort_order, icon),
        )
        db.commit()
        last_id = cursor.lastrowid
        db.close()
        return last_id

    @staticmethod
    def update_type_full(
        type_id: int, name: str, slug: str, sort_order: int = 0, icon: str = ""
    ) -> None:
        db = get_calc_db()
        db.execute(
            "UPDATE product_types SET name=?, slug=?, sort_order=?, icon=? WHERE id=?",
            (name, slug, sort_order, icon, type_id),
        )
        db.commit()
        db.close()

    @staticmethod
    def get_subtype_full(subtype_id: int) -> sqlite3.Row | None:
        db = get_calc_db()
        row = db.execute(
            """SELECT ps.*, pt.name as type_name
               FROM product_subtypes ps
               JOIN product_types pt ON ps.product_type_id = pt.id
               WHERE ps.id=?""",
            (subtype_id,),
        ).fetchone()
        db.close()
        return row

    @staticmethod
    def update_subtype_full(
        subtype_id: int,
        type_id: int,
        name: str,
        slug: str,
        formula: str,
        has_flange: bool = False,
        labor_norm: float = 0.0,
        waste_factor: float = 1.0,
        shape: str = "rect",
        description: str = "",
    ) -> None:
        db = get_calc_db()
        db.execute(
            """UPDATE product_subtypes SET
                product_type_id=?, name=?, slug=?, formula=?, has_flange=?,
                labor_norm=?, waste_factor=?, shape=?, description=?
                WHERE id=?""",
            (
                type_id,
                name,
                slug,
                formula,
                int(has_flange),
                labor_norm,
                waste_factor,
                shape,
                description,
                subtype_id,
            ),
        )
        db.commit()
        db.close()

    @staticmethod
    def delete_subtype_full(subtype_id: int) -> None:
        db = get_calc_db()
        db.execute("DELETE FROM size_ranges WHERE subtype_id=?", (subtype_id,))
        db.execute("DELETE FROM subtype_materials WHERE subtype_id=?", (subtype_id,))
        db.execute("DELETE FROM product_subtypes WHERE id=?", (subtype_id,))
        db.commit()
        db.close()
