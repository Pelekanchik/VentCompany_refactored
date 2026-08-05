#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Виправляє неправильні імпорти в gui.py"""

import os
import re

# Папка з gui.py
gui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ventilation_company', 'gui.py')

if not os.path.exists(gui_path):
    print(f"❌ gui.py не знайдено: {gui_path}")
    exit(1)

print(f"Читаємо: {gui_path}")

with open(gui_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Знаходимо всі неправильні імпорти
# Шаблон: ventilation_company.ventilation_company.XXX
pattern = r'ventilation_company\.ventilation_company\.ventilation_company\.([a-zA-Z_][a-zA-Z0-9_]*)'
matches = re.findall(pattern, content)

if matches:
    print(f"Знайдено неправильні імпорти: {matches}")
    # Замінюємо
    fixed = re.sub(pattern, r'ventilation_company.', content)

    # Резервна копія
    backup = gui_path + '.backup'
    with open(backup, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Резервна копія: {backup}")

    # Зберігаємо виправлений
    with open(gui_path, 'w', encoding='utf-8') as f:
        f.write(fixed)
    print(f"✅ gui.py виправлено!")

    # Показуємо зміни
    print("\nЗміни:")
    for m in set(matches):
        print(f"  ❌ ventilation_company.ventilation_company.{m}")
        print(f"  ✅ ventilation_company.{m}")
else:
    print("Не знайдено неправильних імпортів.")
