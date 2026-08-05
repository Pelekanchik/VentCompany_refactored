"""
Репозиторій для роботи з розрахунками (КП)
"""
import sqlite3
import json
from typing import List, Dict, Any, Optional
from ventilation_company.database import get_calc_db


class CalcRepo:
    """CRUD для calc_calculations, calc_items"""

    # ── calc_calculations ──
    @staticmethod
    def get_all_calculations() -> List[sqlite3.Row]:
        db = get_calc_db()
        rows = db.execute(
            "SELECT * FROM calc_calculations ORDER BY created_at DESC"
        ).fetchall()
        db.close()
        return rows

    @staticmethod
    def get_calculation_by_id(calc_id: int) -> Optional[sqlite3.Row]:
        db = get_calc_db()
        row = db.execute(
            "SELECT * FROM calc_calculations WHERE id=?", (calc_id,)
        ).fetchone()
        db.close()
        return row

    @staticmethod
    def get_calculations_by_client(client_name: str) -> List[sqlite3.Row]:
        db = get_calc_db()
        rows = db.execute(
            "SELECT * FROM calc_calculations WHERE client_name LIKE ? ORDER BY created_at DESC",
            (f"%{client_name}%",)
        ).fetchall()
        db.close()
        return rows

    @staticmethod
    def get_calculations_by_period(start_date: str, end_date: str) -> List[sqlite3.Row]:
        db = get_calc_db()
        rows = db.execute(
            """SELECT * FROM calc_calculations
               WHERE created_at BETWEEN ? AND ?
               ORDER BY created_at DESC""",
            (start_date, end_date)
        ).fetchall()
        db.close()
        return rows

    @staticmethod
    def add_calculation(client_name: str, client_phone: str = "",
                        markup_percent: float = 30.0, overhead_percent: float = 15.0,
                        notes: str = "") -> int:
        db = get_calc_db()
        from datetime import datetime
        now = datetime.now().isoformat()
        try:
            cursor = db.execute(
                """INSERT INTO calc_calculations
                   (client_name, client_phone, markup_percent, overhead_percent,
                    created_at, updated_at, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (client_name, client_phone, markup_percent, overhead_percent, now, now, notes)
            )
        except sqlite3.OperationalError:
            # Fallback для старої схеми без updated_at/notes
            cursor = db.execute(
                """INSERT INTO calc_calculations
                   (client_name, client_phone, markup_percent, overhead_percent, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (client_name, client_phone, markup_percent, overhead_percent, now)
            )
        db.commit()
        last_id = cursor.lastrowid
        db.close()
        return last_id

    @staticmethod
    def update_calculation(calc_id: int, **kwargs) -> None:
        db = get_calc_db()
        allowed = {"client_name", "client_phone", "markup_percent",
                   "overhead_percent", "notes", "status"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            db.close()
            return
        from datetime import datetime
        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k}=?" for k in fields)
        values = list(fields.values()) + [calc_id]
        db.execute(f"UPDATE calc_calculations SET {set_clause} WHERE id=?", values)
        db.commit()
        db.close()

    @staticmethod
    def delete_calculation(calc_id: int) -> None:
        db = get_calc_db()
        db.execute("DELETE FROM calc_items WHERE calculation_id=?", (calc_id,))
        db.execute("DELETE FROM calc_calculations WHERE id=?", (calc_id,))
        db.commit()
        db.close()

    # ── calc_items ──
    @staticmethod
    def get_items_by_calculation(calc_id: int) -> List[sqlite3.Row]:
        db = get_calc_db()
        rows = db.execute(
            "SELECT * FROM calc_items WHERE calculation_id=?", (calc_id,)
        ).fetchall()
        db.close()
        return rows

    @staticmethod
    def add_item(calculation_id: int, subtype_id: int, material_id: int,
                 size_params: Dict[str, Any], quantity: int = 1,
                 area: float = 0.0, has_flange: bool = False,
                 flange_qty: int = 0, flange_perimeter: float = 0.0,
                 material_cost: float = 0.0, labor_cost: float = 0.0,
                 overhead_cost: float = 0.0, total_cost: float = 0.0,
                 unit_price: float = 0.0, total_price: float = 0.0) -> int:
        db = get_calc_db()
        cursor = db.execute(
            """INSERT INTO calc_items
               (calculation_id, subtype_id, material_id, size_params,
                quantity, area, has_flange, flange_qty, flange_perimeter,
                material_cost, labor_cost, overhead_cost, total_cost,
                unit_price, total_price)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (calculation_id, subtype_id, material_id, json.dumps(size_params),
             quantity, area, int(has_flange), flange_qty, flange_perimeter,
             material_cost, labor_cost, overhead_cost, total_cost,
             unit_price, total_price)
        )
        db.commit()
        last_id = cursor.lastrowid
        db.close()
        return last_id

    @staticmethod
    def update_item(item_id: int, **kwargs) -> None:
        db = get_calc_db()
        allowed = {"subtype_id", "material_id", "size_params", "quantity",
                   "area", "has_flange", "flange_qty", "flange_perimeter",
                   "material_cost", "labor_cost", "overhead_cost",
                   "total_cost", "unit_price", "total_price"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            db.close()
            return
        if "size_params" in fields:
            fields["size_params"] = json.dumps(fields["size_params"])
        set_clause = ", ".join(f"{k}=?" for k in fields)
        values = list(fields.values()) + [item_id]
        db.execute(f"UPDATE calc_items SET {set_clause} WHERE id=?", values)
        db.commit()
        db.close()

    @staticmethod
    def delete_item(item_id: int) -> None:
        db = get_calc_db()
        db.execute("DELETE FROM calc_items WHERE id=?", (item_id,))
        db.commit()
        db.close()

    @staticmethod
    def delete_items_by_calculation(calc_id: int) -> None:
        db = get_calc_db()
        db.execute("DELETE FROM calc_items WHERE calculation_id=?", (calc_id,))
        db.commit()
        db.close()

    @staticmethod
    def get_calculation_with_items(calc_id: int) -> tuple:
        db = get_calc_db()
        calc = db.execute("SELECT * FROM calc_calculations WHERE id=?", (calc_id,)).fetchone()
        items = db.execute("""
            SELECT ci.*, ps.name as subtype_name, m.name as material_name, m.thickness
            FROM calc_items ci
            JOIN product_subtypes ps ON ci.subtype_id = ps.id
            JOIN calc_materials m ON ci.material_id = m.id
            WHERE ci.calculation_id=?
        """, (calc_id,)).fetchall()
        db.close()
        return calc, items

    @staticmethod
    def update_calculation_full(calc_id: int, total_cost: float = None,
                                 sale_price: float = None, status: str = None) -> None:
        db = get_calc_db()
        fields = []
        values = []
        if total_cost is not None:
            fields.append("total_cost=?")
            values.append(total_cost)
        if sale_price is not None:
            fields.append("sale_price=?")
            values.append(sale_price)
        if status is not None:
            fields.append("status=?")
            values.append(status)
        if fields:
            from datetime import datetime
            try:
                # Нова схема з updated_at
                fields_new = fields + ["updated_at=?"]
                values_new = values + [datetime.now().isoformat(), calc_id]
                db.execute(f"UPDATE calc_calculations SET {', '.join(fields_new)} WHERE id=?", values_new)
            except sqlite3.OperationalError:
                # Стара схема без updated_at
                values.append(calc_id)
                db.execute(f"UPDATE calc_calculations SET {', '.join(fields)} WHERE id=?", values)
            db.commit()
        db.close()

    @staticmethod
    def get_calculations_by_period(start_date: str, end_date: str):
        db = get_calc_db()
        rows = db.execute(
            "SELECT * FROM calc_calculations WHERE created_at BETWEEN ? AND ? ORDER BY created_at DESC",
            (start_date, end_date)
        ).fetchall()
        db.close()
        return rows

    @staticmethod
    def get_calculations_summary():
        db = get_calc_db()
        rows = db.execute("""
            SELECT c.*, COUNT(ci.id) as item_count, SUM(ci.total_price) as calc_total
            FROM calc_calculations c
            LEFT JOIN calc_items ci ON c.id = ci.calculation_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """).fetchall()
        db.close()
        return rows

