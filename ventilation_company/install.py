#!/usr/bin/env python3
"""
install.py — Автоматична установка інтеграції FreeCAD
"""
import os
import shutil


def find_project_dir():
    """Знайти директорію проекту ventilation_company"""
    current = os.getcwd()

    # Шукаємо вгору по дереву
    while current != "/":
        if os.path.exists(os.path.join(current, "ventilation_company")):
            return os.path.join(current, "ventilation_company")
        current = os.path.dirname(current)

    # Шукаємо в поточній директорії
    if os.path.exists("ventilation_company"):
        return os.path.abspath("ventilation_company")

    return None


def install():
    print("🏗️ Установка інтеграції FreeCAD")
    print("=" * 50)

    project_dir = find_project_dir()
    if not project_dir:
        print("❌ Не знайдено директорію ventilation_company")
        print("   Запустіть скрипт з кореня проекту")
        return False

    print(f"📁 Знайдено проект: {project_dir}")

    # Копіюємо файли
    files_to_copy = [
        ("freecad_exporter.py", "freecad_exporter.py"),
        ("check_freecad.py", "check_freecad.py"),
    ]

    script_dir = os.path.dirname(os.path.abspath(__file__))

    for src_name, dst_name in files_to_copy:
        src = os.path.join(script_dir, src_name)
        dst = os.path.join(project_dir, dst_name)

        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"   ✅ {src_name} → {dst}")
        else:
            print(f"   ⚠️ {src_name} не знайдено")

    # Резервна копія старого CAD
    cad_path = os.path.join(project_dir, "cad_editor.py")
    if os.path.exists(cad_path):
        backup = os.path.join(project_dir, "cad_editor_backup.py")
        shutil.copy2(cad_path, backup)
        print(f"   💾 Резервна копія: {backup}")

    # Копіюємо оновлений CAD
    new_cad = os.path.join(script_dir, "cad_editor_with_freecad.py")
    if os.path.exists(new_cad):
        # Перейменовуємо у cad_editor.py
        dst_cad = os.path.join(project_dir, "cad_editor.py")
        shutil.copy2(new_cad, dst_cad)
        print("   ✅ Оновлено cad_editor.py з підтримкою FreeCAD")

    print("\n🎉 Установка завершена!")
    print("\nНаступні кроки:")
    print("   1. python check_freecad.py")
    print("   2. Запустіть вашу програму")
    print("   3. Відкрийте вкладку 'Креслення'")
    print("   4. Натисніть 🏗 для експорту у FreeCAD")

    return True


if __name__ == "__main__":
    install()
