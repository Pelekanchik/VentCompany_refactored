#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Діагностичний лаунчер VentCompany"""

import sys
import os

# Папка з цим скриптом (3-й рівень)
script_dir = os.path.dirname(os.path.abspath(__file__))

# Додаємо її до шляху
sys.path.insert(0, script_dir)

print("=== ДІАГНОСТИКА ШЛЯХІВ ===")
print(f"Папка скрипта: {script_dir}")
print(f"Python version: {sys.version}")
print()
print("sys.path:")
for i, p in enumerate(sys.path[:5]):
    print(f"  [{i}] {p}")
print()

# Перевіряємо структуру
vc_path = os.path.join(script_dir, 'ventilation_company')
print(f"Папка ventilation_company існує: {os.path.exists(vc_path)}")
if os.path.exists(vc_path):
    print(f"Вміст: {os.listdir(vc_path)}")
    gui_path = os.path.join(vc_path, 'gui.py')
    print(f"gui.py існує: {os.path.exists(gui_path)}")
    dc_path = os.path.join(vc_path, 'detail_calculator.py')
    print(f"detail_calculator.py існує: {os.path.exists(dc_path)}")
print()

# Спробуємо імпортувати detail_calculator окремо
print("=== ТЕСТ 1: detail_calculator ===")
try:
    from ventilation_company import detail_calculator
    print("✅ detail_calculator імпортовано!")
except Exception as e:
    import traceback
    print(f"❌ Помилка: {e}")
    traceback.print_exc()
print()

# Спробуємо імпортувати gui
print("=== ТЕСТ 2: gui ===")
try:
    from ventilation_company import gui
    print("✅ gui імпортовано!")
    print("Запуск gui.main()...")
    gui.main()
except Exception as e:
    import traceback
    print(f"❌ Помилка: {e}")
    traceback.print_exc()
