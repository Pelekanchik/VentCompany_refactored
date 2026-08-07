#!/usr/bin/env python3
"""
Автоматичне виправлення VentCompany_refactored.
Замінює product.py та price_list_tab.py на модифіковані версії.

ЗАПУСК (з кореня VentCompany_refactored/):
    python apply_fix.py
"""

import os
import shutil

# Шляхи до файлів
FILES = {
    "ventilation_company/models/product.py": {
        "backup": "ventilation_company/models/product.py.backup",
        "check": ["self.formula", "self.auto_price", "self.metal_price_per_m2"],
    },
    "ventilation_company/price_list_tab.py": {
        "backup": "ventilation_company/price_list_tab.py.backup",
        "check": ["_open_formula_editor", "FORMULA_ENGINE_AVAILABLE"],
    },
}


def check_file(filepath, checks):
    """Перевіряє, чи є потрібні рядки у файлі."""
    if not os.path.exists(filepath):
        return False, "Файл не існує"
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        missing = [c for c in checks if c not in content]
        if missing:
            return False, f"Відсутні: {', '.join(missing)}"
        return True, "OK"
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 60)
    print("  ВИПРАВЛЕННЯ VentCompany_refactored")
    print("=" * 60)

    # Перевіряємо, чи ми в корені проєкту
    if not os.path.exists("ventilation_company"):
        print("\n❌ ПОМИЛКА: Запустіть цей скрипт з кореня проєкту!")
        print("   Поточна папка: " + os.getcwd())
        print("   Очікується: C:\\Users\\Admin\\Desktop\\VentCompany_refactored\\")
        input("\nНатисніть Enter...")
        return

    all_ok = True

    for filepath, info in FILES.items():
        print(f"\n📄 {filepath}")
        ok, msg = check_file(filepath, info["check"])

        if ok:
            print(f"   ✅ {msg} — виправлення не потрібне")
            continue

        print(f"   ❌ {msg}")

        # Шукаємо модифіковану версію поруч
        modified_name = os.path.basename(filepath).replace(".py", "_modified.py")
        modified_path = os.path.join(os.path.dirname(filepath) or ".", modified_name)

        # Або в корені
        root_modified = os.path.join(".", modified_name)

        source = None
        if os.path.exists(modified_path):
            source = modified_path
        elif os.path.exists(root_modified):
            source = root_modified

        if source:
            print(f"   📥 Знайдено модифіковану версію: {source}")

            # Бекап
            if os.path.exists(filepath):
                shutil.copy2(filepath, info["backup"])
                print(f"   💾 Бекап: {info['backup']}")

            # Копіюємо
            shutil.copy2(source, filepath)
            print("   ✅ Замінено!")
        else:
            print("   ❌ Модифіковану версію НЕ ЗНАЙДЕНО!")
            print(f"   Очікувалось: {modified_path} або {root_modified}")
            all_ok = False

    # Видаляємо кеш
    print("\n🧹 Видалення кешу Python...")
    cache_dirs = [
        "ventilation_company/__pycache__",
        "ventilation_company/models/__pycache__",
        "ventilation_company/gui/__pycache__",
    ]
    for d in cache_dirs:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
                print(f"   ✅ Видалено: {d}")
            except Exception as e:
                print(f"   ⚠️ Не вдалося видалити {d}: {e}")

    print("\n" + "=" * 60)
    if all_ok:
        print("🎉 ГОТОВО! Перезапустіть програму:")
        print("   python main.py")
    else:
        print("⚠️  Деякі файли не вдалося оновити.")
        print("   Завантажте файли за посиланнями та покладіть у відповідні папки.")

    input("\nНатисніть Enter...")


if __name__ == "__main__":
    main()
