"""
Розрахунок зарплатного фонду
"""

from datetime import datetime

from ventilation_company.config import POSITIONS
from ventilation_company.database import execute_query


class SalaryCalculator:
    PIT_RATE = 18.0
    MILITARY_TAX = 1.5
    ESV_RATE = 22.0

    def __init__(self):
        self.employees = []

    def add_employee(self, full_name, position, base_salary=None, bonus_percent=None):
        pos_data = POSITIONS.get(position)
        if not pos_data:
            print(f"Posada '{position}' ne znajdena")
            return None
        salary = base_salary if base_salary is not None else pos_data["ставка"]
        bonus = bonus_percent if bonus_percent is not None else pos_data["премія_%"]
        employee = {
            "full_name": full_name,
            "position": position,
            "base_salary": salary,
            "bonus_percent": bonus,
            "bonus_amount": salary * (bonus / 100),
            "total_salary": salary + salary * (bonus / 100),
        }
        self.employees.append(employee)
        return employee

    def calculate_employee_net(self, total_salary):
        pit = total_salary * (self.PIT_RATE / 100)
        military = total_salary * (self.MILITARY_TAX / 100)
        total_taxes = pit + military
        net_salary = total_salary - total_taxes
        esv = total_salary * (self.ESV_RATE / 100)
        return {
            "gross_salary": round(total_salary, 2),
            "pit": round(pit, 2),
            "military_tax": round(military, 2),
            "total_taxes": round(total_taxes, 2),
            "net_salary": round(net_salary, 2),
            "esv": round(esv, 2),
            "total_employer_cost": round(total_salary + esv, 2),
        }

    def calculate_payroll(self, year=None, month=None):
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        payroll_details = []
        total_gross = 0
        total_taxes = 0
        total_net = 0
        total_esv = 0
        total_employer_cost = 0
        for emp in self.employees:
            calc = self.calculate_employee_net(emp["total_salary"])
            detail = {
                "full_name": emp["full_name"],
                "position": emp["position"],
                "base_salary": emp["base_salary"],
                "bonus_percent": emp["bonus_percent"],
                "bonus_amount": round(emp["bonus_amount"], 2),
                **calc,
            }
            payroll_details.append(detail)
            total_gross += calc["gross_salary"]
            total_taxes += calc["total_taxes"]
            total_net += calc["net_salary"]
            total_esv += calc["esv"]
            total_employer_cost += calc["total_employer_cost"]
        return {
            "year": year,
            "month": month,
            "employees_count": len(self.employees),
            "details": payroll_details,
            "total_gross": round(total_gross, 2),
            "total_pit": round(sum(d["pit"] for d in payroll_details), 2),
            "total_military_tax": round(sum(d["military_tax"] for d in payroll_details), 2),
            "total_taxes": round(total_taxes, 2),
            "total_net": round(total_net, 2),
            "total_esv": round(total_esv, 2),
            "total_employer_cost": round(total_employer_cost, 2),
        }

    def save_to_db(self, year=None, month=None):
        result = self.calculate_payroll(year, month)
        for detail in result["details"]:
            emp_query = "SELECT id FROM employees WHERE full_name = ?"
            emp_row = execute_query(emp_query, (detail["full_name"],), fetch_one=True)
            if emp_row:
                employee_id = emp_row[0]
            else:
                insert_emp = """
                    INSERT INTO employees (full_name, position, base_salary, bonus_percent, actual_salary, hired_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                employee_id = execute_query(
                    insert_emp,
                    (
                        detail["full_name"],
                        detail["position"],
                        detail["base_salary"],
                        detail["bonus_percent"],
                        detail["gross_salary"],
                        datetime.now().isoformat(),
                    ),
                )
            insert_payroll = """
                INSERT INTO payroll (year, month, employee_id, base_salary, bonus_amount, total_salary, taxes, net_salary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            execute_query(
                insert_payroll,
                (
                    result["year"],
                    result["month"],
                    employee_id,
                    detail["base_salary"],
                    detail["bonus_amount"],
                    detail["gross_salary"],
                    detail["total_taxes"],
                    detail["net_salary"],
                ),
            )
        print("Zarplatnyj fond zberezheno v BD")
        return result

    def print_payroll(self, year=None, month=None):
        result = self.calculate_payroll(year, month)
        print("\n" + "=" * 90)
        print("ZARPLATNYJ FOND".center(90))
        print(f"za {result['month']}.{result['year']}".center(90))
        print("=" * 90)
        print(
            f"{'PIB':<25} {'Posada':<18} {'Bazova':<12} {'Premija':<10} {'Vsogo':<12} {'Podatky':<10} {'Na ruky':<12}"
        )
        print("-" * 90)
        for emp in result["details"]:
            print(
                f"{emp['full_name']:<25} {emp['position']:<18} "
                f"{emp['base_salary']:<12.2f} {emp['bonus_amount']:<10.2f} "
                f"{emp['gross_salary']:<12.2f} {emp['total_taxes']:<10.2f} "
                f"{emp['net_salary']:<12.2f}"
            )
        print("-" * 90)
        print(f"VSOHO SPIVROBITNYKIV: {result['employees_count']}")
        print(f"ZAHALNYJ FOND (gross): {result['total_gross']:>15.2f} hrn")
        print(f"PDF (18%):             {result['total_pit']:>15.2f} hrn")
        print(f"Vijskovyj zbir (1.5%): {result['total_military_tax']:>15.2f} hrn")
        print(f"ESV (22%):             {result['total_esv']:>15.2f} hrn")
        print("=" * 90)
        print(f"VSOHO VYTRATY ROBOTODAVCJA: {result['total_employer_cost']:>15.2f} hrn")
        print(f"CHYSTA ZARPLATA:            {result['total_net']:>15.2f} hrn")
        print("=" * 90)

    @staticmethod
    def get_payroll_history(year=None, month=None):
        if year and month:
            query = """
                SELECT p.year, p.month, e.full_name, e.position,
                       p.base_salary, p.bonus_amount, p.total_salary, p.taxes, p.net_salary
                FROM payroll p
                JOIN employees e ON p.employee_id = e.id
                WHERE p.year = ? AND p.month = ?
                ORDER BY p.total_salary DESC
            """
            return execute_query(query, (year, month))
        else:
            query = """
                SELECT p.year, p.month, e.full_name, e.position,
                       p.base_salary, p.bonus_amount, p.total_salary, p.taxes, p.net_salary
                FROM payroll p
                JOIN employees e ON p.employee_id = e.id
                ORDER BY p.year DESC, p.month DESC, p.total_salary DESC
            """
            return execute_query(query)
