#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПАТЧ БАЗИ ДАНИХ КАЛЬКУЛЯТОРА
Додає колонку project_id у таблицю calc_calculations
Запустіть один раз!
"""

import sqlite3
import os
import sys

# --- Знайдемо шлях до БД калькулятора ---
# Шукаємо ventilation_company/database.py або calc_database.db
possible_paths = [
    os.path.join(os.path.dirname(__file__), "ventilation_company", "calc_database.db"),
    os.path.join(os.path.dirname(__file__), "calc_database.db"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "ventilation_company", "calc_database.db"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "calc_database.db"),
]

# Якщо є пакет ventilation_company, спробуємо імпортувати
DB_PATH = None
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ventilation_company.database import get_calc_db
    db = get_calc_db()
    # Отримаємо шлях до файлу БД
    cursor = db.execute("PRAGMA database_list")
    for row in cursor:
        if row[1] == "main":
            DB_PATH = row[2]
            break
    db.close()
except Exception as e:
    print(f"Не вдалося імпортувати get_calc_db: {e}")

# Якщо не вдалося через імпорт — шукаємо вручну
if not DB_PATH:
    for p in possible_paths:
        if os.path.exists(p):
            DB_PATH = p
            break

if not DB_PATH:
    print("❌ Не знайдено файл calc_database.db")
    print("   Переконайтесь, що скрипт знаходиться в корені проекту.")
    print("   Або вкажіть шлях вручну у змінній DB_PATH у цьому файлі.")
    input("Натисніть Enter для виходу...")
    sys.exit(1)

print(f"✅ Знайдено БД: {DB_PATH}")

# --- Додаємо колонку ---
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Перевіримо чи колонка вже існує
c.execute("PRAGMA table_info(calc_calculations)")
columns = [row[1] for row in c.fetchall()]

if "project_id" in columns:
    print("ℹ️ Колонка project_id ВЖЕ існує. Нічого робити не треба.")
else:
    c.execute("ALTER TABLE calc_calculations ADD COLUMN project_id INTEGER")
    conn.commit()
    print("✅ Колонка project_id успішно додана!")

# Перевіримо ще раз
c.execute("PRAGMA table_info(calc_calculations)")
columns = [row[1] for row in c.fetchall()]
print(f"   Колонки таблиці: {', '.join(columns)}")

conn.close()
print("\n🎉 Готово! Тепер можна запускати програму.")
input("Натисніть Enter для виходу...")
