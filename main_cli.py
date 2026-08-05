#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Консольний інтерфейс
"""

import os
import sys

from ventilation_company.database import init_database
from ventilation_company.models.project import Project
from ventilation_company.project_builder.project import ProjectService
from ventilation_company.project_builder.components import ComponentCatalog, DuctCalculator
from ventilation_company.project_builder.specifications import SpecificationBuilder
from ventilation_company.project_builder.export import ProjectExporter
from ventilation_company.calculations.cost_calculator import CostCalculator
from ventilation_company.calculations.salary_calculator import SalaryCalculator
from ventilation_company.calculations.expenses import ExpenseTracker, ProductionCostAnalyzer
from ventilation_company.calculations.pricing import PricingEngine
from ventilation_company.archive.storage import ArchiveStorage
from ventilation_company.archive.analytics import ProductionAnalytics
from ventilation_company.archive.statistics import ProductionStatistics
from ventilation_company.archive.reports import ReportGenerator
from ventilation_company.utils.archive_manager import ArchiveManager


def print_menu():
    print("\n" + "=" * 60)
    print("ВЕНТИЛЯЦІЙНА ВИРОБНИЧА ФІРМА".center(60))
    print("=" * 60)
    print("""
    МОДУЛЬ 1: ПОБУДОВА ПРОЕКТУ
       1. Створити новий проект
       2. Додати компоненти
       3. Додати матеріали
       4. Додати роботи
       5. Переглянути специфікацію
       6. Експортувати проект
       7. Розрахунок повітропроводів
       8. Переглянути каталог

    МОДУЛЬ 2: РОЗРАХУНКИ
       9. Розрахувати вартість
      10. Розрахувати зарплатний фонд
      11. Облік витрат
      12. Ціноутворення
      13. Аналіз собівартості

    МОДУЛЬ 3: АРХІВ ТА АНАЛІТИКА
      14. Архівувати проект
      15. Переглянути архів
      16. Аналітика
      17. Статистика
      18. Звіти

       0. Вихід
    """)
    print("=" * 60)


def demo_create_project():
    print("\nСТВОРЕННЯ НОВОГО ПРОЕКТУ")
    project = Project(
        name="Вентиляція офісного центру",
        client="ТОВ 'Горизонт'",
        address="м. Київ, вул. Хрещатик, 15",
        ventilation_type="припливно-витяжна",
        air_flow=8500,
        pressure=450
    )
    valid, errors = project.validate()
    if valid:
        project.save_to_db()
        print(f"Проект створено: {project}")
        return project
    return None


def demo_add_components(project):
    components = [
        ("вентилятор_радіальний", 2, "шт", 8500),
        ("фільтр_грубої_очистки", 2, "шт", 1200),
        ("фільтр_тонкої_очистки", 2, "шт", 2800),
        ("клапан_вогнезатримуючий", 4, "шт", 5600),
        ("гнучка_вставка", 6, "шт", 850),
        ("решітка_вентиляційна", 12, "шт", 450),
        ("дифузор", 8, "шт", 680),
        ("шумоглушник", 2, "шт", 3200),
        ("калорифер", 1, "шт", 15000),
    ]
    for name, qty, unit, price in components:
        project.add_component(name, qty, unit, price)


def demo_add_materials(project):
    calc = DuctCalculator()
    rect1 = calc.calculate_rectangular_duct(400, 250, 45, "оцинкована_сталь_0.7")
    rect2 = calc.calculate_rectangular_duct(315, 200, 32, "оцинкована_сталь_0.7")
    round1 = calc.calculate_round_duct(250, 28, "оцинкована_сталь_0.7")
    materials = [
        ("оцинкована_сталь_0.7", rect1["area_m2"] + rect2["area_m2"] + round1["area_m2"], "м²", 580),
        ("ізоляція_мінвата", rect1["area_m2"] + rect2["area_m2"] + round1["area_m2"], "м²", 180),
    ]
    for name, qty, unit, price in materials:
        project.add_material(name, qty, unit, price)


def demo_add_works(project):
    total_area = 185.5
    works = [
        ("виготовлення_повітропроводу", total_area, "м²", 850),
        ("монтаж_повітропроводу", total_area, "м²", 420),
        ("монтаж_вентилятора", 2, "шт", 2500),
        ("монтаж_фільтра", 4, "шт", 800),
        ("монтаж_клапана", 4, "шт", 1500),
        ("ізоляція_повітропроводу", total_area, "м²", 280),
        ("пусконалагоджувальні_роботи", 1, "система", 15000),
        ("балансування_системи", 1, "система", 8000),
    ]
    for name, qty, unit, price in works:
        project.add_work(name, qty, unit, price)


def demo_calculations(project):
    calc = CostCalculator(project)
    calc.print_calculation()
    calc.save_calculation()
    return calc.calculate()


def demo_salary():
    calc = SalaryCalculator()
    employees = [
        ("Іваненко Петро", "директор"),
        ("Петренко Олег", "головний_інженер"),
        ("Сидоренко Марія", "інженер_проектувальник"),
        ("Коваленко Андрій", "технолог"),
        ("Мельник Сергій", "зварник"),
        ("Шевченко Василь", "монтажник"),
        ("Бондаренко Ігор", "електрик"),
        ("Ткаченко Олена", "бухгалтер"),
        ("Гриценко Дмитро", "менеджер_з_продажу"),
    ]
    for name, position in employees:
        calc.add_employee(name, position)
    calc.print_payroll()
    calc.save_to_db()


def demo_archive(project):
    exporter = ProjectExporter(project)
    files = exporter.export_all(include_archive=True)
    storage = ArchiveStorage()
    if project.id:
        storage.archive_project(project.id, project.project_number, files)
    return files


def demo_analytics():
    analytics = ProductionAnalytics()
    analytics.print_dashboard()


def demo_reports():
    reporter = ReportGenerator()
    reporter.generate_financial_report()
    reporter.generate_projects_report()
    reporter.generate_full_report()
    print("Звіти згенеровано!")


def run_full_demo():
    print("\nЗАПУСК ПОВНОЇ ДЕМОНСТРАЦІЇ")
    init_database()
    project = demo_create_project()
    if not project:
        return
    demo_add_components(project)
    demo_add_materials(project)
    demo_add_works(project)
    spec = SpecificationBuilder(project)
    spec.print_specification()
    calc_result = demo_calculations(project)
    demo_salary()
    demo_archive(project)
    demo_analytics()
    demo_reports()
    print("\nДЕМОНСТРАЦІЮ ЗАВЕРШЕНО!")


def main():
    init_database()
    while True:
        print_menu()
        choice = input("   Оберіть дію (0-18 або 'demo'): ").strip().lower()
        if choice == "0":
            print("До побачення!")
            break
        elif choice == "demo":
            run_full_demo()
        elif choice == "1":
            name = input("   Назва: ")
            client = input("   Замовник: ")
            address = input("   Адреса: ")
            vtype = input("   Тип: ")
            airflow = float(input("   Витрата: ") or 0)
            pressure = float(input("   Тиск: ") or 0)
            project = Project(name, client, address, vtype, airflow, pressure)
            if project.validate()[0]:
                project.save_to_db()
                print(f"Проект {project.project_number} створено!")
        elif choice == "7":
            calc = DuctCalculator()
            shape = input("   Форма (round/rectangular): ").strip()
            if shape == "round":
                d = int(input("   Діаметр (мм): "))
                l = float(input("   Довжина (м): "))
                result = calc.calculate_round_duct(d, l)
            else:
                w = int(input("   Ширина (мм): "))
                h = int(input("   Висота (мм): "))
                l = float(input("   Довжина (м): "))
                result = calc.calculate_rectangular_duct(w, h, l)
            for key, val in result.items():
                print(f"      {key}: {val}")
        elif choice == "8":
            ComponentCatalog.print_catalog()
        elif choice == "9":
            pid = int(input("   ID проекту: "))
            project = ProjectService.load_from_db(pid)
            if project:
                CostCalculator(project).print_calculation()
        elif choice == "10":
            demo_salary()
        elif choice == "14":
            pid = int(input("   ID проекту: "))
            project = ProjectService.load_from_db(pid)
            if project:
                storage = ArchiveStorage()
                files = ProjectExporter(project).export_all()
                storage.archive_project(pid, project.project_number, files)
        elif choice == "15":
            ArchiveStorage().print_archives()
        elif choice == "16":
            demo_analytics()
        elif choice == "18":
            demo_reports()
        else:
            print("Функція в розробці")
        input("\nНатисніть Enter...")


if __name__ == "__main__":
    main()
