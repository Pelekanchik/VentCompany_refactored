r"""
Демонстрація використання всіх модулів разом.
Показує повний цикл: вироби → розкрій → специфікація → збереження в БД.

Запуск:
    cd C:\Users\Admin\Desktop\VentCompany_refactored
    python -m ventilation_company.demo_usage
"""

import os
import sys

# Додаємо корінь проєкту в шлях (для надійності при будь-якому запуску)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ventilation_company.auto_specification import SpecBuilder
from ventilation_company.db_integration import ProjectDatabase, save_project_full
from ventilation_company.metal_cutting import MetalCutter
from ventilation_company.standard_products import (
    MaterialType,
    ProductLibrary,
    RectCap,
    RectElbow,
    RectFlange,
    RectTee,
    RectTransition,
    RoundFlange,
    Thickness,
    make_rect_duct,
    make_round_duct,
)


def demo():
    print("=" * 70)
    print("🏭 ДЕМОНСТРАЦІЯ VentCompany — Повний цикл")
    print("=" * 70)

    # =========================================================
    # 1. СТВОРЮЄМО БІБЛІОТЕКУ ВИРОБІВ
    # =========================================================
    print("\n📦 1. Створення бібліотеки стандартних виробів")
    print("-" * 50)

    lib = ProductLibrary()

    # Повітропроводи
    lib.add(make_rect_duct(400, 200, 1500, thickness=0.7, quantity=5))
    lib.add(make_rect_duct(500, 300, 2000, thickness=0.9, quantity=3))
    lib.add(make_round_duct(250, 3000, thickness=0.7, quantity=4))

    # Фланці
    lib.add(
        RectFlange(
            name="Фланець 400×200",
            width=400,
            height=200,
            length=0,
            thickness=Thickness.T1_0,
            material=MaterialType.GALVANIZED,
            quantity=10,
            flange_border=30,
        )
    )
    lib.add(
        RoundFlange(
            name="Фланець Ø250",
            width=250,
            height=250,
            length=0,
            thickness=Thickness.T1_0,
            material=MaterialType.GALVANIZED,
            quantity=8,
            flange_width=30,
        )
    )

    # Трійники
    lib.add(
        RectTee(
            name="Трійник 400×200/200×200",
            width=400,
            height=200,
            length=800,
            thickness=Thickness.T0_9,
            material=MaterialType.GALVANIZED,
            quantity=2,
            branch_width=200,
            branch_height=200,
            branch_length=400,
        )
    )

    # Переходи
    lib.add(
        RectTransition(
            name="Перехід 500×300→400×200",
            width=500,
            height=300,
            length=400,
            thickness=Thickness.T0_9,
            material=MaterialType.GALVANIZED,
            quantity=1,
            end_width=400,
            end_height=200,
        )
    )

    # Відводи
    lib.add(
        RectElbow(
            name="Відвід 400×200 90°",
            width=400,
            height=200,
            length=300,
            thickness=Thickness.T0_7,
            material=MaterialType.GALVANIZED,
            quantity=4,
            angle=90,
            radius=150,
        )
    )

    # Заглушки
    lib.add(
        RectCap(
            name="Заглушка 400×200",
            width=400,
            height=200,
            length=0,
            thickness=Thickness.T0_7,
            material=MaterialType.GALVANIZED,
            quantity=2,
            flange_border=25,
        )
    )

    print(f"   Додано виробів: {len(lib)}")
    print(f"   Загальна площа металу: {lib.get_total_metal_area():.3f} м²")
    print(f"   Загальна вага: {lib.get_total_weight():.3f} кг")

    print("\n   📋 Згрупована специфікація:")
    for item in lib.get_specification():
        print(
            f"      {item['type']:<30} {item['dimensions']:<15} ×{item['quantity']:<4} "
            f"{item['total_area_m2']:.3f} м²  {item['total_weight_kg']:.3f} кг"
        )

    # =========================================================
    # 2. РОЗРАХУНОК РОЗКРОЮ
    # =========================================================
    print("\n\n✂️ 2. Розрахунок розкрою металу")
    print("-" * 50)

    cutter = MetalCutter(sheet_width=1250, sheet_height=2500, thickness=0.7)
    products_for_cutting = lib.to_dict()
    plan = cutter.calculate_from_products(products_for_cutting)

    print(f"   Листів потрібно: {plan.total_sheets}")
    print(f"   Загальна площа листів: {plan.total_area:.3f} м²")
    print(f"   Використано: {plan.total_used_area:.3f} м²")
    print(f"   Відходи: {plan.total_waste_area:.3f} м²")
    print(f"   Коефіцієнт використання: {plan.overall_utilization*100:.1f}%")

    if plan.unplaced_details:
        print(f"   ⚠️ Не розміщено деталей: {len(plan.unplaced_details)}")

    # =========================================================
    # 3. СПЕЦИФІКАЦІЯ
    # =========================================================
    print("\n\n📋 3. Формування специфікації")
    print("-" * 50)

    builder = SpecBuilder(project_name="Вентиляція офісу №42", project_id="VENT-2026-042")

    builder.set_material_price("оцинкована сталь", 55.0)
    builder.set_material_price("нержавіюча сталь", 180.0)

    for p in products_for_cutting:
        builder.add_product(p)

    spec = builder.build()

    print(f"   Позицій: {spec.total_items}")
    print(f"   Загальна кількість: {spec.total_quantity} шт")
    print(f"   Загальна вага: {spec.total_weight:.3f} кг")
    print(f"   Загальна площа: {spec.total_area:.3f} м²")
    print(f"   Загальна вартість: {spec.total_price:.2f} грн")

    print("\n   📊 Зведення за типами:")
    for s in spec.get_summary_by_type():
        print(
            f"      {s['product_type']:<30} {s['total_quantity']:<5} шт  "
            f"{s['total_weight_kg']:.2f} кг  {s['total_price']:.2f} грн"
        )

    print("\n   🔧 Зведення за матеріалами:")
    for s in spec.get_summary_by_material():
        print(
            f"      {s['material']} {s['thickness_mm']} мм: {s['total_quantity']} шт, "
            f"{s['total_weight_kg']:.2f} кг"
        )

    # =========================================================
    # 4. ЗБЕРЕЖЕННЯ В БД
    # =========================================================
    print("\n\n💾 4. Збереження в базу даних")
    print("-" * 50)

    db = ProjectDatabase("data/company.db")

    result = save_project_full(
        project_name="Вентиляція офісу №42",
        products=products_for_cutting,
        spec_data=spec.to_dict(),
        cutting_plan=plan.to_dict(),
        db_path="data/company.db",
    )

    print(f"   ✅ Проєкт збережено з ID: {result['project_id']}")
    print(f"   📋 Специфікація ID: {result['specification_id']}")
    print(f"   ✂️ План розкрою ID: {result['cutting_plan_id']}")
    print(f"   📦 Кількість виробів: {result['products_count']}")

    project = db.get_project(result["project_id"])
    summary = db.get_project_summary(result["project_id"])

    print("\n   📊 Зведення з БД:")
    print(f"      Назва: {project['name']}")
    print(f"      Позицій: {summary.get('total_items', 0)}")
    print(f"      Кількість: {summary.get('total_quantity', 0)}")
    print(f"      Вага: {summary.get('total_weight', 0):.3f} кг")
    print(f"      Площа: {summary.get('total_area', 0):.3f} м²")

    # =========================================================
    # 5. ЕКСПОРТ
    # =========================================================
    print("\n\n📤 5. Експорт специфікації")
    print("-" * 50)

    os.makedirs("output", exist_ok=True)

    builder.save_to_file("output/spec.json", format="json")
    builder.save_to_file("output/spec.csv", format="csv")
    builder.save_to_file("output/spec.txt", format="txt")
    builder.save_to_file("output/spec.html", format="html")

    print("   ✅ spec.json — машиночитаний формат")
    print("   ✅ spec.csv — для Excel/Google Таблиць")
    print("   ✅ spec.txt — текстовий звіт")
    print("   ✅ spec.html — для друку/перегляду в браузері")

    print("\n" + "=" * 70)
    print("✅ Демонстрація завершена успішно!")
    print("=" * 70)

    return result


if __name__ == "__main__":
    demo()
