"""
Модуль генерації звітів
"""

import os
from datetime import datetime

from ventilation_company.config import REPORTS_DIR
from ventilation_company.database import execute_query


class ReportGenerator:
    def __init__(self):
        os.makedirs(REPORTS_DIR, exist_ok=True)

    def generate_financial_report(self, year=None, month=None, filepath=None):
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(REPORTS_DIR, f"financial_report_{timestamp}.txt")
        query = """
            SELECT COUNT(*) as projects, SUM(materials_cost) as materials,
                   SUM(components_cost) as components, SUM(works_cost) as works,
                   SUM(total_cost) as cost, SUM(final_price) as revenue, SUM(profit) as profit
            FROM calculations
        """
        row = execute_query(query, fetch_one=True)
        lines = []
        lines.append("=" * 70)
        lines.append("ФІНАНСОВИЙ ЗВІТ".center(70))
        lines.append(f"Сформовано: {datetime.now().strftime('%d.%m.%Y %H:%M')}".center(70))
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Кількість розрахунків: {row[0] or 0}")
        lines.append("")
        lines.append("ВИТРАТИ:")
        lines.append(f"  Матеріали:           {row[1] or 0:>15.2f} грн")
        lines.append(f"  Комплектуючі:        {row[2] or 0:>15.2f} грн")
        lines.append(f"  Роботи:              {row[3] or 0:>15.2f} грн")
        lines.append(
            f"  Накладні витрати:    {(row[4] or 0) - (row[1] or 0) - (row[2] or 0) - (row[3] or 0):>15.2f} грн"
        )
        lines.append("-" * 70)
        lines.append(f"  СОБІВАРТІСТЬ:        {row[4] or 0:>15.2f} грн")
        lines.append("")
        lines.append("ДОХОДИ:")
        lines.append(f"  Виручка:             {row[5] or 0:>15.2f} грн")
        lines.append(f"  Прибуток:            {row[6] or 0:>15.2f} грн")
        lines.append(f"  Рентабельність:      {((row[6] or 0) / (row[5] or 1) * 100):>15.2f} %")
        lines.append("=" * 70)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Фінансовий звіт збережено: {filepath}")
        return filepath

    def generate_projects_report(self, filepath=None):
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(REPORTS_DIR, f"projects_report_{timestamp}.txt")
        projects = execute_query(
            """
            SELECT p.project_number, p.name, p.client, p.ventilation_type,
                   p.status, p.created_at, c.final_price, c.profit
            FROM projects p
            LEFT JOIN calculations c ON p.id = c.project_id
            ORDER BY p.created_at DESC
        """
        )
        lines = []
        lines.append("=" * 100)
        lines.append("ЗВІТ ПО ПРОЄКТАХ".center(100))
        lines.append(f"Сформовано: {datetime.now().strftime('%d.%m.%Y %H:%M')}".center(100))
        lines.append("=" * 100)
        lines.append("")
        lines.append(
            f"{'№':<5} {'Номер':<12} {'Назва':<20} {'Замовник':<15} {'Тип':<18} {'Статус':<10} {'Ціна':<12} {'Прибуток':<12}"
        )
        lines.append("-" * 100)
        for i, proj in enumerate(projects, 1):
            lines.append(
                f"{i:<5} {proj[0]:<12} {proj[1]:<20} {str(proj[2]):<15} {proj[3]:<18} "
                f"{proj[4]:<10} {proj[6] or 0:<12.2f} {proj[7] or 0:<12.2f}"
            )
        lines.append("=" * 100)
        lines.append(f"Всього проєктів: {len(projects)}")
        lines.append("=" * 100)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Звіт по проєктах збережено: {filepath}")
        return filepath

    def generate_salary_report(self, year=None, month=None, filepath=None):
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(REPORTS_DIR, f"salary_report_{timestamp}.txt")
        if year and month:
            payroll = execute_query(
                """
                SELECT e.full_name, e.position, p.base_salary, p.bonus_amount,
                       p.total_salary, p.taxes, p.net_salary
                FROM payroll p
                JOIN employees e ON p.employee_id = e.id
                WHERE p.year = ? AND p.month = ?
                ORDER BY p.total_salary DESC
            """,
                (year, month),
            )
        else:
            payroll = execute_query(
                """
                SELECT e.full_name, e.position, p.year, p.month, p.base_salary,
                       p.bonus_amount, p.total_salary, p.taxes, p.net_salary
                FROM payroll p
                JOIN employees e ON p.employee_id = e.id
                ORDER BY p.year DESC, p.month DESC, p.total_salary DESC
            """
            )
        lines = []
        lines.append("=" * 100)
        lines.append("ЗВІТ ПО ЗАРПЛАТІ".center(100))
        lines.append(f"Сформовано: {datetime.now().strftime('%d.%m.%Y %H:%M')}".center(100))
        lines.append("=" * 100)
        lines.append("")
        if year and month:
            lines.append(
                f"{'ПІБ':<25} {'Посада':<18} {'Базова':<12} {'Премія':<10} {'Всього':<12} {'Податки':<10} {'На руки':<12}"
            )
            lines.append("-" * 100)
            for row in payroll:
                lines.append(
                    f"{row[0]:<25} {row[1]:<18} {row[2]:<12.2f} {row[3]:<10.2f} {row[4]:<12.2f} {row[5]:<10.2f} {row[6]:<12.2f}"
                )
        else:
            lines.append(
                f"{'ПІБ':<25} {'Посада':<18} {'Рік':<6} {'Міс':<5} {'Базова':<12} {'Премія':<10} {'Всього':<12} {'На руки':<12}"
            )
            lines.append("-" * 100)
            for row in payroll:
                lines.append(
                    f"{row[0]:<25} {row[1]:<18} {row[2]:<6} {row[3]:<5} {row[4]:<12.2f} {row[5]:<10.2f} {row[6]:<12.2f} {row[8]:<12.2f}"
                )
        lines.append("=" * 100)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Звіт по зарплаті збережено: {filepath}")
        return filepath

    def generate_full_report(self, filepath=None):
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(REPORTS_DIR, f"full_report_{timestamp}.txt")
        lines = []
        lines.append("=" * 80)
        lines.append("ЗВЕДЕНИЙ ЗВІТ ПРО ДІЯЛЬНІСТЬ ПІДПРИЄМСТВА".center(80))
        lines.append(f"Сформовано: {datetime.now().strftime('%d.%m.%Y %H:%M')}".center(80))
        lines.append("=" * 80)
        lines.append("")
        projects_count = execute_query("SELECT COUNT(*) FROM projects", fetch_one=True)[0]
        lines.append("ПРОЄКТИ")
        lines.append(f"   Всього проєктів у системі: {projects_count}")
        lines.append("")
        fin = execute_query(
            "SELECT SUM(final_price), SUM(profit), SUM(total_cost) FROM calculations",
            fetch_one=True,
        )
        lines.append("ФІНАНСИ")
        lines.append(f"   Загальна виручка: {fin[0] or 0:,.2f} грн")
        lines.append(f"   Загальний прибуток: {fin[1] or 0:,.2f} грн")
        lines.append(f"   Загальна собівартість: {fin[2] or 0:,.2f} грн")
        lines.append("")
        emp_count = execute_query("SELECT COUNT(*) FROM employees", fetch_one=True)[0]
        lines.append("ПЕРСОНАЛ")
        lines.append(f"   Кількість співробітників: {emp_count}")
        lines.append("")
        prod = execute_query(
            "SELECT SUM(completed_quantity), SUM(defects_quantity), SUM(hours_spent) FROM production",
            fetch_one=True,
        )
        lines.append("ВИРОБНИЦТВО")
        lines.append(f"   Виготовлено: {prod[0] or 0:.2f}")
        lines.append(f"   Брак: {prod[1] or 0:.2f}")
        lines.append(f"   Витрачено годин: {prod[2] or 0:.2f}")
        lines.append("")
        lines.append("=" * 80)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Зведений звіт збережено: {filepath}")
        return filepath
