"""
Сервіс розрахунків виробів вентиляції
Бізнес-логіка без GUI
"""

from math import pi
from typing import Any

from ventilation_company.database.repositories.calc_repo import CalcRepo
from ventilation_company.database.repositories.settings_repo import SettingsRepo


class CalculatorService:
    """Сервіс для розрахунку вартості виробів вентиляції."""

    @staticmethod
    def calculate_area(formula: str, params: dict[str, float], waste_factor: float = 1.0) -> float:
        """Обчислює площу за формулою."""
        expr = formula.replace("pi", str(pi)).replace("π", str(pi))
        for key, val in params.items():
            expr = expr.replace(key, str(float(val)))
        try:
            return eval(expr, {"__builtins__": {}}, {"pi": pi}) * waste_factor
        except Exception as e:
            print(f"Помилка формули '{formula}': {e}")
            return 0.0

    @staticmethod
    def calculate_item_cost(
        area: float,
        material_price_per_m2: float,
        labor_rate: float,
        labor_mode: str = "m2",
        labor_norm: float = 0.0,
        quantity: int = 1,
        overhead_percent: float = 15.0,
    ) -> dict[str, float]:
        """Розраховує собівартість однієї позиції."""
        material_cost = area * material_price_per_m2

        labor_cost = area * labor_rate if labor_mode == "m2" else labor_norm * labor_rate

        overhead_cost = (material_cost + labor_cost) * (overhead_percent / 100)
        total_cost = material_cost + labor_cost + overhead_cost

        return {
            "material_cost": material_cost,
            "labor_cost": labor_cost,
            "overhead_cost": overhead_cost,
            "total_cost": total_cost,
        }

    @staticmethod
    def apply_markup(total_cost: float, markup_percent: float) -> float:
        """Застосовує націнку."""
        return total_cost * (1 + markup_percent / 100)

    @staticmethod
    def apply_group_discount(
        unit_price: float, total_qty: int, discount_table: dict[int, float]
    ) -> float:
        """Застосовує групову знижку за кількістю."""
        discount = 0.0
        for threshold, pct in sorted(discount_table.items(), key=lambda x: int(x[0])):
            if total_qty >= int(threshold):
                discount = float(pct)
        if discount > 0:
            return unit_price * (1 - discount / 100)
        return unit_price

    @staticmethod
    def get_flange_cost(perimeter: float, price_per_m: float) -> float:
        """Розраховує вартість фланця."""
        return perimeter * price_per_m

    @staticmethod
    def get_labor_rate() -> float:
        """Повертає ставку роботи з налаштувань."""
        return SettingsRepo.get_float("labor_rate", 850.0)

    @staticmethod
    def get_markup_percent() -> float:
        """Повертає відсоток націнки з налаштувань."""
        return SettingsRepo.get_float("markup_percent", 30.0)

    @staticmethod
    def get_overhead_percent() -> float:
        """Повертає відсоток накладних витрат."""
        return SettingsRepo.get_float("overhead_percent", 15.0)

    @staticmethod
    def get_flange_price() -> float:
        """Повертає ціну фланця за метр."""
        return SettingsRepo.get_float("flange_price_per_m", 120.0)

    @staticmethod
    def get_monthly_production_qty() -> int:
        """Повертає місячний обсяг виробництва."""
        return SettingsRepo.get_int("monthly_production_qty", 100)

    @staticmethod
    def get_calculation_summary(calc_id: int) -> dict[str, Any] | None:
        """Повертає підсумок розрахунку."""
        calc = CalcRepo.get_calculation_by_id(calc_id)
        if not calc:
            return None

        items = CalcRepo.get_items_by_calculation(calc_id)
        total_cost = sum(item["total_cost"] * item["quantity"] for item in items)
        total_price = sum(item["total_price"] for item in items)

        return {
            "calculation": dict(calc),
            "items": [dict(item) for item in items],
            "total_cost": total_cost,
            "total_price": total_price,
            "item_count": len(items),
        }

    @staticmethod
    def compare_calculations(calc_ids: list[int]) -> list[dict[str, Any]]:
        """Порівнює кілька розрахунків."""
        results = []
        for cid in calc_ids:
            summary = CalculatorService.get_calculation_summary(cid)
            if summary:
                results.append(summary)
        return results
