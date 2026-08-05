"""
Розрахунок вартості проекту
"""
from ventilation_company.config import MARKUP_PERCENTAGE, VAT_RATE, OVERHEAD_PERCENTAGE
from ventilation_company.database import execute_query


class CostCalculator:
    def __init__(self, project):
        self.project = project
        self.calculation_id = None

    def calculate(self):
        materials_cost = sum(m["total_price"] for m in self.project._materials)
        components_cost = sum(c["total_price"] for c in self.project._components)
        works_cost = sum(w["total_price"] for w in self.project._works)
        direct_costs = materials_cost + components_cost + works_cost
        overhead_cost = direct_costs * (OVERHEAD_PERCENTAGE / 100)
        total_cost = direct_costs + overhead_cost
        markup_amount = total_cost * (MARKUP_PERCENTAGE / 100)
        price_without_vat = total_cost + markup_amount
        vat_amount = price_without_vat * (VAT_RATE / 100)
        final_price = price_without_vat + vat_amount
        profit = markup_amount
        return {
            "project_id": self.project.id,
            "project_number": self.project.project_number,
            "materials_cost": round(materials_cost, 2),
            "components_cost": round(components_cost, 2),
            "works_cost": round(works_cost, 2),
            "direct_costs": round(direct_costs, 2),
            "overhead_cost": round(overhead_cost, 2),
            "overhead_percentage": OVERHEAD_PERCENTAGE,
            "total_cost": round(total_cost, 2),
            "markup_amount": round(markup_amount, 2),
            "markup_percentage": MARKUP_PERCENTAGE,
            "price_without_vat": round(price_without_vat, 2),
            "vat_amount": round(vat_amount, 2),
            "vat_rate": VAT_RATE,
            "final_price": round(final_price, 2),
            "profit": round(profit, 2),
            "profit_margin_percent": round((profit / final_price) * 100, 2) if final_price > 0 else 0
        }

    def save_calculation(self):
        result = self.calculate()
        from datetime import datetime
        query = """
            INSERT INTO calculations
            (project_id, calculation_type, materials_cost, components_cost, works_cost,
             overhead_cost, total_cost, markup_amount, vat_amount, final_price, profit, calculated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            result["project_id"], "full", result["materials_cost"], result["components_cost"],
            result["works_cost"], result["overhead_cost"], result["total_cost"],
            result["markup_amount"], result["vat_amount"], result["final_price"],
            result["profit"], datetime.now().isoformat()
        )
        self.calculation_id = execute_query(query, params)
        print(f"Rozrakhunok zberezheno (ID: {self.calculation_id})")
        return self.calculation_id

    def print_calculation(self):
        result = self.calculate()
        print("\n" + "=" * 70)
        print("ROZRAKHUNOK VARTOSTI PROEKTU".center(70))
        print("=" * 70)
        print(f"  Proekt: {result['project_number']}")
        print("-" * 70)
        print(f"  1. Materialy:          {result['materials_cost']:>15.2f} hrn")
        print(f"  2. Komplektuuchi:      {result['components_cost']:>15.2f} hrn")
        print(f"  3. Roboty:             {result['works_cost']:>15.2f} hrn")
        print("-" * 70)
        print(f"  PRIAMI VYTRATY:        {result['direct_costs']:>15.2f} hrn")
        print(f"  4. Nakladni ({OVERHEAD_PERCENTAGE}%):    {result['overhead_cost']:>15.2f} hrn")
        print("=" * 70)
        print(f"  SOBIVARTIST:           {result['total_cost']:>15.2f} hrn")
        print("-" * 70)
        print(f"  5. Nacinka ({MARKUP_PERCENTAGE}%):      {result['markup_amount']:>15.2f} hrn")
        print(f"  Cina bez PDV:          {result['price_without_vat']:>15.2f} hrn")
        print(f"  6. PDV ({VAT_RATE}%):           {result['vat_amount']:>15.2f} hrn")
        print("=" * 70)
        print(f"  KINCEVA CINA (z PDV):  {result['final_price']:>15.2f} hrn")
        print("=" * 70)
        print(f"  PRYBUTOK:              {result['profit']:>15.2f} hrn")
        print(f"  Rentabelnist:          {result['profit_margin_percent']:>15.2f} %")
        print("=" * 70)

    @staticmethod
    def get_project_calculations(project_id):
        query = "SELECT * FROM calculations WHERE project_id = ? ORDER BY calculated_at DESC"
        return execute_query(query, (project_id,))
