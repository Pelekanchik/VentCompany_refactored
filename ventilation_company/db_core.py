"""
Модуль роботи з базою даних SQLite
"""

import json
import os
import sqlite3
from math import pi

from ventilation_company.config import DB_PATH


def init_database():
    """Ініціалізація бази даних - створення всіх таблиць"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_number TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            client TEXT,
            address TEXT,
            ventilation_type TEXT,
            air_flow REAL,
            pressure REAL,
            created_at TEXT,
            updated_at TEXT,
            status TEXT DEFAULT 'draft',
            total_area REAL DEFAULT 0,
            notes TEXT
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS project_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            component_name TEXT,
            quantity REAL,
            unit TEXT,
            unit_price REAL,
            total_price REAL,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS project_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            material_name TEXT,
            quantity REAL,
            unit TEXT,
            unit_price REAL,
            total_price REAL,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS project_works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            work_name TEXT,
            quantity REAL,
            unit TEXT,
            unit_price REAL,
            total_price REAL,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            calculation_type TEXT,
            materials_cost REAL DEFAULT 0,
            components_cost REAL DEFAULT 0,
            works_cost REAL DEFAULT 0,
            overhead_cost REAL DEFAULT 0,
            total_cost REAL DEFAULT 0,
            markup_amount REAL DEFAULT 0,
            vat_amount REAL DEFAULT 0,
            final_price REAL DEFAULT 0,
            profit REAL DEFAULT 0,
            calculated_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            position TEXT,
            base_salary REAL,
            bonus_percent REAL DEFAULT 0,
            actual_salary REAL,
            hired_date TEXT,
            status TEXT DEFAULT 'active'
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            month INTEGER,
            employee_id INTEGER,
            base_salary REAL,
            bonus_amount REAL,
            total_salary REAL,
            taxes REAL,
            net_salary REAL,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS production (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            production_date TEXT,
            stage TEXT,
            completed_quantity REAL,
            defects_quantity REAL DEFAULT 0,
            hours_spent REAL,
            responsible_employee TEXT,
            notes TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            archive_name TEXT,
            project_id INTEGER,
            file_path TEXT,
            file_size INTEGER,
            created_at TEXT,
            archive_type TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """
    )

    # ========== ТАБЛИЦЯ КРЕСЛЕНЬ ПРОЕКТУ ==========
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS project_drawings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            drawing_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_drawings_project ON project_drawings(project_id)"
    )

    # ========== ТАБЛИЦІ КАЛЬКУЛЯТОРА ВИРОБІВ ==========
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS product_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            icon TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS product_subtypes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_type_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            formula TEXT NOT NULL,
            shape_type TEXT DEFAULT 'round',
            flange_perimeter_formula TEXT,
            waste_factor REAL DEFAULT 1.18,
            labor_norm REAL DEFAULT 0.5,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (product_type_id) REFERENCES product_types(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS size_ranges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtype_id INTEGER NOT NULL,
            param_name TEXT NOT NULL,
            param_label TEXT NOT NULL,
            min_value REAL,
            max_value REAL,
            step REAL,
            unit TEXT DEFAULT 'мм',
            values_json TEXT,
            FOREIGN KEY (subtype_id) REFERENCES product_subtypes(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS calc_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grade TEXT,
            thickness REAL NOT NULL,
            unit TEXT DEFAULT 'мм',
            price_per_m2 REAL NOT NULL,
            waste_factor REAL DEFAULT 1.18,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS subtype_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtype_id INTEGER NOT NULL,
            material_id INTEGER NOT NULL,
            is_default INTEGER DEFAULT 0,
            UNIQUE(subtype_id, material_id),
            FOREIGN KEY (subtype_id) REFERENCES product_subtypes(id) ON DELETE CASCADE,
            FOREIGN KEY (material_id) REFERENCES calc_materials(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS calc_calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            client_phone TEXT,
            markup_percent REAL DEFAULT 30,
            overhead_percent REAL DEFAULT 15,
            labor_mode TEXT DEFAULT 'hour',
            total_cost REAL DEFAULT 0,
            sale_price REAL DEFAULT 0,
            status TEXT DEFAULT 'draft',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS calc_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calculation_id INTEGER NOT NULL,
            subtype_id INTEGER NOT NULL,
            material_id INTEGER NOT NULL,
            size_params TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            area_m2 REAL DEFAULT 0,
            material_cost REAL DEFAULT 0,
            flange_cost REAL DEFAULT 0,
            labor_cost REAL DEFAULT 0,
            overhead_cost REAL DEFAULT 0,
            total_cost REAL DEFAULT 0,
            unit_price REAL DEFAULT 0,
            total_price REAL DEFAULT 0,
            FOREIGN KEY (calculation_id) REFERENCES calc_calculations(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS overhead_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT DEFAULT 'fixed',
            value REAL NOT NULL,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS calc_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """
    )

    # Заповнення демо-даних калькулятора (тільки якщо таблиці порожні)
    cursor.execute("SELECT COUNT(*) FROM product_types")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO product_types (name, slug, icon, sort_order) VALUES (?,?,?,?)",
            [
                ("Повітропроводи", "ducts", "🔧", 1),
                ("Фасонні вироби", "fittings", "🔩", 2),
                ("Решітки та дифузори", "grilles", "⬜", 3),
                ("Заслінки та клапани", "dampers", "🔲", 4),
            ],
        )

    cursor.execute("SELECT COUNT(*) FROM product_subtypes")
    if cursor.fetchone()[0] == 0:

        cursor.executemany(
            """
            INSERT INTO product_subtypes (product_type_id, name, slug, formula, shape_type, flange_perimeter_formula, waste_factor, labor_norm, description)
            VALUES (?,?,?,?,?,?,?,?,?)
        """,
            [
                (
                    1,
                    "Круглі повітропроводи",
                    "round_duct",
                    "pi * (diameter/1000 + 2*0.003) * (length/1000)",
                    "round",
                    None,
                    1.18,
                    0.35,
                    "Круглого перерізу з фальцевим з'єднанням",
                ),
                (
                    1,
                    "Прямокутні повітропроводи",
                    "rect_duct",
                    "2 * (width/1000 + height/1000 + 2*0.003) * (length/1000)",
                    "rect",
                    "2 * (width/1000 + height/1000)",
                    1.20,
                    0.45,
                    "Прямокутного перерізу",
                ),
                (
                    2,
                    "Відведення (коліно)",
                    "elbow",
                    "pi * (diameter/1000 + 2*0.003) * (diameter/1000) * 1.35",
                    "round",
                    None,
                    1.25,
                    0.60,
                    "Кругле відведення",
                ),
                (
                    2,
                    "Трійник",
                    "tee",
                    "pi * (diameter/1000 + 2*0.003) * (diameter/1000) * 1.55",
                    "round",
                    None,
                    1.28,
                    0.90,
                    "Круглий трійник",
                ),
                (
                    2,
                    "Перехід",
                    "transition",
                    "pi * ((d1/1000 + d2/1000)/2 + 2*0.003) * (length/1000) * 1.25",
                    "round",
                    None,
                    1.25,
                    0.70,
                    "Перехід діаметра",
                ),
                (
                    2,
                    "Заглушка",
                    "cap",
                    "pi * (diameter/1000 + 2*0.003) * (diameter/1000) * 0.8",
                    "round",
                    None,
                    1.22,
                    0.30,
                    "Заглушка кругла",
                ),
                (
                    2,
                    "Прямокутне відведення",
                    "rect_elbow",
                    "2 * (width/1000 + height/1000 + 2*0.003) * ((width/1000 + height/1000)/2) * 1.35",
                    "rect",
                    "2 * (width/1000 + height/1000)",
                    1.25,
                    0.65,
                    "Прямокутне коліно",
                ),
                (
                    2,
                    "Прямокутний трійник",
                    "rect_tee",
                    "2 * (width/1000 + height/1000 + 2*0.003) * ((width/1000 + height/1000)/2) * 1.65",
                    "rect",
                    "2 * (width/1000 + height/1000)",
                    1.28,
                    0.95,
                    "Прямокутний трійник",
                ),
                (
                    2,
                    "Прямокутний перехід",
                    "rect_transition",
                    "2 * ((width/1000 + height/1000 + width2/1000 + height2/1000)/2 + 2*0.003) * (length/1000) * 1.3",
                    "rect",
                    "2 * (width/1000 + height/1000)",
                    1.25,
                    0.75,
                    "Перехід прямокутного перерізу",
                ),
                (
                    2,
                    "Прямокутна заглушка",
                    "rect_cap",
                    "2 * (width/1000 + height/1000 + 2*0.003) * ((width/1000 + height/1000)/2) * 0.75",
                    "rect",
                    "2 * (width/1000 + height/1000)",
                    1.22,
                    0.35,
                    "Заглушка прямокутна",
                ),
                (
                    3,
                    "Решітка вентиляційна",
                    "grille",
                    "(width/1000) * (height/1000) * 2.5",
                    "rect",
                    None,
                    1.15,
                    0.40,
                    "Решітка з ламелями",
                ),
                (
                    4,
                    "Заслінка повітряна",
                    "damper",
                    "pi * (diameter/1000 + 2*0.003) * (diameter/1000) * 1.8",
                    "round",
                    None,
                    1.25,
                    0.55,
                    "Ручна заслінка",
                ),
            ],
        )

    cursor.execute("SELECT COUNT(*) FROM size_ranges")
    if cursor.fetchone()[0] == 0:

        cursor.executemany(
            """
            INSERT INTO size_ranges (subtype_id, param_name, param_label, min_value, max_value, step, unit, values_json)
            VALUES (?,?,?,?,?,?,?,?)
        """,
            [
                (
                    1,
                    "diameter",
                    "Діаметр",
                    80,
                    1000,
                    10,
                    "мм",
                    json.dumps([80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000]),
                ),
                (1, "length", "Довжина", 100, 3000, 50, "мм", None),
                (
                    2,
                    "width",
                    "Ширина",
                    100,
                    1000,
                    50,
                    "мм",
                    json.dumps([100, 150, 200, 250, 300, 400, 500, 600, 800]),
                ),
                (
                    2,
                    "height",
                    "Висота",
                    50,
                    500,
                    50,
                    "мм",
                    json.dumps([50, 100, 150, 200, 250, 300, 400]),
                ),
                (2, "length", "Довжина", 100, 3000, 50, "мм", None),
                (
                    3,
                    "diameter",
                    "Діаметр",
                    80,
                    1000,
                    10,
                    "мм",
                    json.dumps([100, 125, 160, 200, 250, 315, 400, 500]),
                ),
                (3, "angle", "Кут", 30, 90, 15, "°", json.dumps([30, 45, 60, 90])),
                (
                    4,
                    "diameter",
                    "Діаметр",
                    100,
                    500,
                    10,
                    "мм",
                    json.dumps([100, 125, 160, 200, 250, 315]),
                ),
                (5, "d1", "Вхідний діаметр", 100, 500, 10, "мм", json.dumps([160, 200, 250, 315])),
                (5, "d2", "Вихідний діаметр", 80, 400, 10, "мм", json.dumps([100, 125, 160, 200])),
                (5, "length", "Довжина", 100, 500, 50, "мм", None),
                (
                    7,
                    "width",
                    "Ширина",
                    100,
                    600,
                    50,
                    "мм",
                    json.dumps([150, 200, 300, 400, 500, 600]),
                ),
                (
                    7,
                    "height",
                    "Висота",
                    100,
                    600,
                    50,
                    "мм",
                    json.dumps([150, 200, 300, 400, 500, 600]),
                ),
                (
                    8,
                    "diameter",
                    "Діаметр",
                    100,
                    500,
                    10,
                    "мм",
                    json.dumps([100, 125, 160, 200, 250, 315]),
                ),
                (
                    9,
                    "width",
                    "Ширина",
                    100,
                    1000,
                    50,
                    "мм",
                    json.dumps([100, 150, 200, 250, 300, 400, 500, 600, 800]),
                ),
                (
                    9,
                    "height",
                    "Висота",
                    50,
                    500,
                    50,
                    "мм",
                    json.dumps([50, 100, 150, 200, 250, 300, 400]),
                ),
                (9, "angle", "Кут", 30, 90, 15, "°", json.dumps([30, 45, 60, 90])),
                (
                    10,
                    "width",
                    "Ширина",
                    100,
                    1000,
                    50,
                    "мм",
                    json.dumps([100, 150, 200, 250, 300, 400, 500, 600, 800]),
                ),
                (
                    10,
                    "height",
                    "Висота",
                    50,
                    500,
                    50,
                    "мм",
                    json.dumps([50, 100, 150, 200, 250, 300, 400]),
                ),
                (
                    11,
                    "width",
                    "Вхідна ширина",
                    100,
                    1000,
                    50,
                    "мм",
                    json.dumps([200, 250, 300, 400, 500, 600, 800]),
                ),
                (
                    11,
                    "height",
                    "Вхідна висота",
                    50,
                    500,
                    50,
                    "мм",
                    json.dumps([100, 150, 200, 250, 300, 400]),
                ),
                (
                    11,
                    "width2",
                    "Вихідна ширина",
                    100,
                    800,
                    50,
                    "мм",
                    json.dumps([100, 150, 200, 250, 300, 400, 500, 600]),
                ),
                (
                    11,
                    "height2",
                    "Вихідна висота",
                    50,
                    400,
                    50,
                    "мм",
                    json.dumps([50, 100, 150, 200, 250, 300]),
                ),
                (11, "length", "Довжина", 100, 500, 50, "мм", None),
                (
                    12,
                    "width",
                    "Ширина",
                    100,
                    1000,
                    50,
                    "мм",
                    json.dumps([100, 150, 200, 250, 300, 400, 500, 600, 800]),
                ),
                (
                    12,
                    "height",
                    "Висота",
                    50,
                    500,
                    50,
                    "мм",
                    json.dumps([50, 100, 150, 200, 250, 300, 400]),
                ),
            ],
        )

    cursor.execute("SELECT COUNT(*) FROM calc_materials")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT INTO calc_materials (name, grade, thickness, price_per_m2, waste_factor)
            VALUES (?,?,?,?,?)
        """,
            [
                ("Оцинкована сталь", "DX51D+Z", 0.5, 420, 1.18),
                ("Оцинкована сталь", "DX51D+Z", 0.7, 580, 1.18),
                ("Оцинкована сталь", "DX51D+Z", 1.0, 790, 1.22),
                ("Нержавіюча сталь", "AISI 304", 0.8, 1450, 1.25),
                ("Нержавіюча сталь", "AISI 304", 1.0, 1800, 1.25),
                ("Нержавіюча сталь", "AISI 430", 0.8, 950, 1.25),
                ("Алюміній", "АД0", 0.8, 1100, 1.22),
                ("Алюміній", "АД0", 1.0, 1350, 1.22),
                ("Чорний метал", "08пс", 1.5, 680, 1.20),
                ("Чорний метал", "08пс", 2.0, 890, 1.20),
                ("Чорний метал", "08пс", 3.0, 1250, 1.20),
            ],
        )

    cursor.execute("SELECT COUNT(*) FROM subtype_materials")
    if cursor.fetchone()[0] == 0:
        for sid in range(1, 13):
            for mid in range(1, 12):
                is_def = 1 if (sid in [1, 2] and mid == 1) or (sid == 3 and mid == 1) else 0
                cursor.execute(
                    "INSERT INTO subtype_materials (subtype_id, material_id, is_default) VALUES (?,?,?)",
                    (sid, mid, is_def),
                )

    cursor.execute("SELECT COUNT(*) FROM calc_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO calc_settings (key, value) VALUES (?,?)", ("monthly_products", "100")
        )
        cursor.execute(
            "INSERT INTO calc_settings (key, value) VALUES (?,?)", ("flange_profile_price", "45")
        )
        cursor.execute(
            "INSERT INTO calc_settings (key, value) VALUES (?,?)", ("flange_corner_price", "35")
        )
        cursor.execute(
            "INSERT INTO calc_settings (key, value) VALUES (?,?)", ("flange_waste_factor", "1.15")
        )

    cursor.execute("SELECT COUNT(*) FROM overhead_items")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO overhead_items (name, type, value) VALUES (?,?,?)",
            [
                ("Оренда цеху", "fixed", 5000),
                ("Електроенергія", "percent", 8),
                ("Амортизація обладнання", "percent", 5),
                ("Інструменти та витратники", "percent", 3),
                ("Транспорт", "percent", 2),
            ],
        )

    conn.execute("PRAGMA journal_mode=WAL;")
    conn.commit()
    conn.close()
    print("Baza danykh inicializovano!")


def get_connection():
    return sqlite3.connect(DB_PATH)


def execute_query(query, params=(), fetch_one=False):
    conn = get_connection()
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        cursor.execute(query, params)
        if query.strip().upper().startswith("SELECT"):
            result = cursor.fetchone() if fetch_one else cursor.fetchall()
            return result
        else:
            conn.commit()
            return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ========== ДОПОМІЖНІ ФУНКЦІЇ КАЛЬКУЛЯТОРА ==========


def get_calc_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def calculate_area(formula: str, params: dict, waste_factor: float) -> float:
    expr = formula.replace("pi", str(pi)).replace("π", str(pi))
    for key, val in params.items():
        expr = expr.replace(key, str(float(val)))
    try:
        return eval(expr, {"__builtins__": {}}, {"pi": pi}) * waste_factor
    except Exception as e:
        print(f"Помилка формули '{formula}': {e}")
        return 0.0


def get_size_labels(subtype_id):
    db = get_calc_db()
    rows = db.execute(
        "SELECT param_name, param_label FROM size_ranges WHERE subtype_id=?", (subtype_id,)
    ).fetchall()
    db.close()
    return {r["param_name"]: r["param_label"] for r in rows}


def format_size_params(size_params_json, subtype_id):
    try:
        params = json.loads(size_params_json)
    except (json.JSONDecodeError, TypeError):
        return size_params_json or "—"
    labels = get_size_labels(subtype_id)
    parts = []
    for key, val in params.items():
        label = labels.get(key, key)
        parts.append(f"{label}: {val}")
    return ", ".join(parts)


if __name__ == "__main__":
    init_database()
