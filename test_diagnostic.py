#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Діагностика запуску detail_calculator"""

import sys
import traceback

print("Python version:", sys.version)
print("Python path:", sys.path[:3])
print()

try:
    print("1. Імпорт ventilation_company.database...")
    from ventilation_company.database import get_calc_db, calculate_area, get_size_labels, format_size_params
    print("   ✅ OK")
except Exception as e:
    print(f"   ❌ ПОМИЛКА: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("2. Імпорт detail_calculator...")
    from ventilation_company.detail_calculator import DetailCalculatorFrame
    print("   ✅ OK")
except Exception as e:
    print(f"   ❌ ПОМИЛКА: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("3. Перевірка методів...")
    required = ['calculate_all', 'build_calculator', 'export_current_xlsx', 'print_current',
                'add_item_to_calc', 'on_calc_type_change', 'on_calc_subtype_change']
    for m in required:
        if hasattr(DetailCalculatorFrame, m):
            print(f"   ✅ {m}")
        else:
            print(f"   ❌ MISSING: {m}")
except Exception as e:
    print(f"   ❌ ПОМИЛКА: {e}")
    traceback.print_exc()

try:
    print("4. Створення фрейму...")
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    frame = DetailCalculatorFrame(root)
    print("   ✅ OK")
    print(f"   Вкладок: {len(frame.notebook.tabs())}")
    frame.destroy()
    root.destroy()
except Exception as e:
    print(f"   ❌ ПОМИЛКА: {e}")
    traceback.print_exc()

print("\nДіагностика завершена.")
