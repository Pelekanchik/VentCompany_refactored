"""
Модуль обліку витрат виробництва
"""
from ventilation_company.database import execute_query
from datetime import datetime


class ExpenseTracker:
    EXPENSE_CATEGORIES = [
        "syrovyna_materialy",
        "komplektuuchi",
        "zarplata_vyrobnyctvo",
        "elektroenerhija",
        "amortyzacija",
        "transport",
        "orenda",
        "inshi"
    ]

    def __init__(self):
        self.expenses = []

    def add_expense(self, category, amount, description="", project_id=None, date=None):
        if category not in self.EXPENSE_CATEGORIES:
            print(f"Kategorija '{category}' ne isnuje")
            return None
        expense = {
            "category": category,
            "amount": float(amount),
            "description": description,
            "project_id": project_id,
            "date": date or datetime.now().isoformat()
        }
        self.expenses.append(expense)
        print(f"  Vytrata dodano: {category} - {amount:.2f} hrn")
        return expense

    def get_total_by_category(self, category=None):
        if category:
            return sum(e["amount"] for e in self.expenses if e["category"] == category)
        return sum(e["amount"] for e in self.expenses)

    def get_summary_by_categories(self):
        summary = {}
        for cat in self.EXPENSE_CATEGORIES:
            total = self.get_total_by_category(cat)
            if total > 0:
                summary[cat] = round(total, 2)
        return summary

    def print_expenses(self):
        print("\n" + "=" * 70)
        print("OBLIK VYTRAT".center(70))
        print("=" * 70)
        for expense in self.expenses:
            print(f"  {expense['date'][:10]} | {expense['category']:<25} | {expense['amount']:>10.2f} hrn | {expense['description']}")
        print("-" * 70)
        summary = self.get_summary_by_categories()
        for cat, total in summary.items():
            print(f"  {cat:<25} {total:>15.2f} hrn")
        print("=" * 70)
        print(f"  VSOHO VYTRAT: {self.get_total_by_category():>15.2f} hrn")
        print("=" * 70)

    def get_monthly_report(self, year, month):
        monthly_expenses = []
        for exp in self.expenses:
            exp_date = datetime.fromisoformat(exp["date"])
            if exp_date.year == year and exp_date.month == month:
                monthly_expenses.append(exp)
        summary = {}
        for cat in self.EXPENSE_CATEGORIES:
            total = sum(e["amount"] for e in monthly_expenses if e["category"] == cat)
            if total > 0:
                summary[cat] = round(total, 2)
        return {
            "year": year,
            "month": month,
            "expenses": monthly_expenses,
            "summary": summary,
            "total": round(sum(summary.values()), 2)
        }


class ProductionCostAnalyzer:
    def __init__(self, project):
        self.project = project

    def analyze_production_cost(self):
        materials_cost = sum(m["total_price"] for m in self.project._materials)
        components_cost = sum(c["total_price"] for c in self.project._components)
        works_cost = sum(w["total_price"] for w in self.project._works)
        direct_costs = materials_cost + components_cost
        from config import OVERHEAD_PERCENTAGE
        overhead = direct_costs * (OVERHEAD_PERCENTAGE / 100)
        production_cost = direct_costs + overhead + works_cost * 0.6
        installation_cost = works_cost * 0.4
        return {
            "project_number": self.project.project_number,
            "materials_cost": round(materials_cost, 2),
            "components_cost": round(components_cost, 2),
            "direct_production_cost": round(direct_costs, 2),
            "overhead": round(overhead, 2),
            "production_cost": round(production_cost, 2),
            "installation_cost": round(installation_cost, 2),
            "total_cost": round(production_cost + installation_cost, 2)
        }

    def print_analysis(self):
        result = self.analyze_production_cost()
        print("\n" + "=" * 70)
        print("ANALIZ SOBIVARTOSTI VYROBNYCTVA".center(70))
        print("=" * 70)
        print(f"  Proekt: {result['project_number']}")
        print("-" * 70)
        print(f"  Materialy:             {result['materials_cost']:>15.2f} hrn")
        print(f"  Komplektuuchi:         {result['components_cost']:>15.2f} hrn")
        print("-" * 70)
        print(f"  Priami vytraty:        {result['direct_production_cost']:>15.2f} hrn")
        print(f"  Nakladni vytraty:      {result['overhead']:>15.2f} hrn")
        print("-" * 70)
        print(f"  Sobivartist vyrobnyctva: {result['production_cost']:>15.2f} hrn")
        print(f"  Sobivartist montazhu:  {result['installation_cost']:>15.2f} hrn")
        print("=" * 70)
        print(f"  ZAHALNA SOBIVARTIST:   {result['total_cost']:>15.2f} hrn")
        print("=" * 70)
