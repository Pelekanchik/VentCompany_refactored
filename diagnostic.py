#!/usr/bin/env python3
"""
Діагностичний скрипт для VentCompany_refactored.
Перевіряє наявність файлів, імпорти та підключення вкладок.

ЗАПУСК:
    python diagnostic.py

Розмістіть цей файл у КОРЕНІ проєкту (там, де main.py / run.py)
"""

import importlib.util
import os
import sys
import traceback

# Кольори для консолі
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}  {text}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}")


def ok(text):
    print(f"{GREEN}✅ {text}{RESET}")


def fail(text):
    print(f"{RED}❌ {text}{RESET}")


def warn(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")


def info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")


# ============================================================
# 1. БАЗОВА ІНФОРМАЦІЯ
# ============================================================
print_header("1. БАЗОВА ІНФОРМАЦІЯ")

print(f"Поточна папка: {os.getcwd()}")
print(f"Python: {sys.version}")
print(f"Платформа: {sys.platform}")

# Шукаємо головний файл
main_files = [f for f in os.listdir(".") if f.endswith(".py") and "main" in f.lower()]
if not main_files:
    main_files = [f for f in os.listdir(".") if f.endswith(".py") and "run" in f.lower()]
if not main_files:
    main_files = [f for f in os.listdir(".") if f.endswith(".py")]

if main_files:
    ok(f"Знайдено Python-файли в корені: {', '.join(main_files)}")
else:
    fail("Не знайдено жодного .py файлу в корені! Ви запускаєте з правильної папки?")
    info("Перейдіть у папку VentCompany_refactored/ і запустіть: python diagnostic.py")

# ============================================================
# 2. ПЕРЕВІРКА ФАЙЛІВ
# ============================================================
print_header("2. ПЕРЕВІРКА НЕОБХІДНИХ ФАЙЛІВ")

required_files = {
    "ventilation_company/formula_engine.py": "Обчислювач формул",
    "ventilation_company/formula_editor_dialog.py": "Редактор формул",
    "ventilation_company/models/product.py": "Модель виробу",
    "ventilation_company/price_list_tab.py": "Вкладка прайс-листа",
    "data/pricing_settings.json": "Налаштування цін",
}

all_ok = True
for path, desc in required_files.items():
    if os.path.exists(path):
        size = os.path.getsize(path)
        ok(f"{desc}: {path} ({size} байт)")
    else:
        fail(f"{desc}: {path} — НЕ ЗНАЙДЕНО!")
        all_ok = False

if not all_ok:
    warn("Не всі файли встановлені. Завантажте їх за посиланнями вище.")

# ============================================================
# 3. ПЕРЕВІРКА ІМПОРТІВ
# ============================================================
print_header("3. ПЕРЕВІРКА ІМПОРТІВ МОДУЛІВ")

modules_to_check = [
    ("ventilation_company.formula_engine", "Обчислювач формул"),
    ("ventilation_company.formula_editor_dialog", "Редактор формул"),
    ("ventilation_company.models.product", "Модель виробу"),
    ("ventilation_company.price_list_tab", "Вкладка прайс-листа"),
]

for module_name, desc in modules_to_check:
    try:
        mod = importlib.import_module(module_name)
        ok(f"{desc}: {module_name} — імпортовано")
    except Exception as e:
        fail(f"{desc}: {module_name} — ПОМИЛКА ІМПОРТУ")
        print(f"   {RED}{str(e)}{RESET}")
        print(f"   {YELLOW}{traceback.format_exc().split('\n')[-4]}{RESET}")

# ============================================================
# 4. ПЕРЕВІРКА ПОЛІВ У PRODUCT
# ============================================================
print_header("4. ПЕРЕВІРКА ПОЛІВ У МОДЕЛІ PRODUCT")

try:
    from ventilation_company.models.product import Product

    required_attrs = ["formula", "auto_price", "metal_price_per_m2", "recalculate_price"]
    for attr in required_attrs:
        if hasattr(Product, attr):
            ok(f"Product має атрибут: {attr}")
        else:
            fail(f"Product НЕ має атрибуту: {attr}")
            warn("Ви замінили product.py? Завантажте product_modified.py")

except Exception as e:
    fail(f"Не вдалося перевірити Product: {e}")

# ============================================================
# 5. ПЕРЕВІРКА PRICE_LIST_TAB
# ============================================================
print_header("5. ПЕРЕВІРКА ВКЛАДКИ ПРАЙС-ЛИСТА")

try:
    from ventilation_company.price_list_tab import PriceListTab

    methods = ["_open_formula_editor", "_get_metal_price_per_m2"]
    for method in methods:
        if hasattr(PriceListTab, method):
            ok(f"PriceListTab має метод: {method}")
        else:
            fail(f"PriceListTab НЕ має методу: {method}")
            warn("Ви замінили price_list_tab.py? Завантажте price_list_tab_modified.py")

    # Перевіряємо наявність FORMULA_ENGINE_AVAILABLE
    import ventilation_company.price_list_tab as plt

    if hasattr(plt, "FORMULA_ENGINE_AVAILABLE"):
        val = plt.FORMULA_ENGINE_AVAILABLE
        if val:
            ok(f"FORMULA_ENGINE_AVAILABLE = {val} (формули УВІМКНЕНО)")
        else:
            warn(f"FORMULA_ENGINE_AVAILABLE = {val} (формули ВИМКНЕНО — помилка імпорту)")
    else:
        fail("FORMULA_ENGINE_AVAILABLE не знайдено — стара версія файлу")

except Exception as e:
    fail(f"Не вдалося перевірити PriceListTab: {e}")

# ============================================================
# 6. ПЕРЕВІРКА ГОЛОВНОГО ВІКНА
# ============================================================
print_header("6. ПОШУК ПІДКЛЮЧЕННЯ ПРАЙС-ЛИСТА")

# Шукаємо у всіх .py файлах згадку про PriceListTab
found = False
for root, _dirs, files in os.walk("."):
    # Пропускаємо папку __pycache__
    if "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, encoding="utf-8") as f:
                    content = f.read()
                if "PriceListTab" in content and "price_list_tab" in content:
                    ok(f"PriceListTab підключено у: {filepath}")
                    found = True
                    # Покажемо рядок
                    for i, line in enumerate(content.split("\n"), 1):
                        if "PriceListTab" in line and not line.strip().startswith("#"):
                            print(f"   {YELLOW}Рядок {i}:{RESET} {line.strip()}")
                            break
            except Exception:
                pass

if not found:
    fail("PriceListTab НЕ знайдено в жодному файлі!")
    warn("Можливо, вкладка прайс-листа ще не підключена до головного вікна.")
    info("Перевірте ваш main.py — чи є там щось на кшталт:")
    info("  from ventilation_company.price_list_tab import PriceListTab")
    info("  PriceListTab(notebook)")

# ============================================================
# 7. ПЕРЕВІРКА СТРУКТУРИ ПАПОК
# ============================================================
print_header("7. СТРУКТУРА ПАПОК")

for root, dirs, files in os.walk(".", topdown=True):
    # Обмежуємо глибину
    depth = root.count(os.sep)
    if depth > 2:
        del dirs[:]
        continue
    if "__pycache__" in root or ".git" in root:
        del dirs[:]
        continue

    indent = "  " * depth
    print(f"{indent}{os.path.basename(root)}/")
    subindent = "  " * (depth + 1)
    for file in sorted(files):
        if file.endswith(".py") or file.endswith(".json"):
            print(f"{subindent}{file}")

# ============================================================
# ВИСНОВОК
# ============================================================
print_header("ВИСНОВОК")

if all_ok:
    ok("Всі необхідні файли знайдено!")
    info("Якщо кнопка '🔧 Формула' не з'являється:")
    info("  1. Закрийте програму повністю")
    info("  2. Відкрийте консоль (cmd / terminal)")
    info("  3. Перейдіть у папку VentCompany_refactored/")
    info("  4. Запустіть: python main.py (або python run.py)")
    info("  5. Подивіться, чи є помилки в консолі")
else:
    fail("Не всі файли встановлені. Завантажте та розмістіть їх за інструкцією.")

print(f"\n{BOLD}Для допомоги надішліть мені повний текст цього виводу.{RESET}\n")

input("Натисніть Enter для виходу...")
