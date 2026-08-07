"""Моделі виробів прайс-листа (Product, PriceHistoryEntry)
З підтримкою формул для автоматичного розрахунку ціни.
"""

from datetime import datetime
from typing import Any


class PriceHistoryEntry:
    """Запис історії зміни ціни."""

    def __init__(self, date: str, old_price: float, new_price: float):
        self.date: str = date
        self.old_price: float = float(old_price)
        self.new_price: float = float(new_price)

    @property
    def diff(self) -> float:
        """Різниця між новою та старою ціною."""
        return round(self.new_price - self.old_price, 2)

    def to_dict(self) -> dict[str, Any]:
        return {"date": self.date, "old_price": self.old_price, "new_price": self.new_price}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PriceHistoryEntry":
        return cls(
            data.get("date", ""), float(data.get("old_price", 0)), float(data.get("new_price", 0))
        )

    def __repr__(self) -> str:
        return f"PriceHistoryEntry({self.date}, {self.old_price} -> {self.new_price})"


class Product:
    """Модель виробу вентиляційної системи.

    Підтримує два режими ціноутворення:
    1. Ручна ціна — price_per_unit встановлюється вручну
    2. Автоматична ціна — розраховується за формулою (formula)
    """

    CATEGORIES = [
        "Вентилятор",
        "Труба прямокутна",
        "Труба кругла",
        "Фасонка",
        "Заслінка",
        "Решітка",
        "Клапан",
        "Комплектуюче",
        "Інше",
    ]

    MATERIALS = ["цинк", "нержавійка", "алюміній"]

    def __init__(
        self,
        product_id: str,
        date_added: str,
        name: str,
        price_per_unit: float = 0.0,
        quantity: float = 1.0,
        length: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
        diameter: float = 0.0,
        material: str = "",
        thickness: float = 0.0,
        category: str = "Інше",
        notes: str = "",
        price_history: list[PriceHistoryEntry] | None = None,
        formula: str = "",
        auto_price: bool = False,
        metal_price_per_m2: float = 0.0,
    ):
        self.id: str = product_id
        self.date_added: str = date_added
        self.name: str = name
        self.price_per_unit: float = float(price_per_unit)
        self.quantity: float = float(quantity)
        self.length: float = float(length) if length else 0.0
        self.width: float = float(width) if width else 0.0
        self.height: float = float(height) if height else 0.0
        self.diameter: float = float(diameter) if diameter else 0.0
        self.material: str = material
        self.thickness: float = float(thickness) if thickness else 0.0
        self.category: str = category if category in self.CATEGORIES else "Інше"
        self.notes: str = notes
        self.price_history: list[PriceHistoryEntry] = price_history or []

        # 🆕 Поля для формульного ціноутворення
        self.formula: str = formula if formula else ""
        self.auto_price: bool = bool(auto_price)
        self.metal_price_per_m2: float = float(metal_price_per_m2)

    @property
    def total_price(self) -> float:
        """Загальна вартість (ціна × кількість)."""
        return round(self.price_per_unit * self.quantity, 2)

    @property
    def date_only(self) -> str:
        """Дата без часу."""
        return self.date_added.split()[0] if self.date_added else ""

    @property
    def dimensions_str(self) -> str:
        """Рядок з розмірами."""
        if self.diameter > 0:
            return f"Ø{self.diameter}"
        parts = []
        if self.length > 0:
            parts.append(f"L{self.length}")
        if self.width > 0:
            parts.append(f"W{self.width}")
        if self.height > 0:
            parts.append(f"H{self.height}")
        return "×".join(parts) if parts else "—"

    @property
    def formula_short(self) -> str:
        """Коротке представлення формули для таблиці."""
        if not self.formula:
            return "—"
        if len(self.formula) > 30:
            return self.formula[:27] + "..."
        return self.formula

    def recalculate_price(self, metal_price_per_m2: float | None = None) -> float:
        """Перерахувати ціну за формулою.

        Args:
            metal_price_per_m2: ціна металу за м². Якщо None — використовує self.metal_price_per_m2

        Returns:
            нова ціна за 1 штуку
        """
        if not self.auto_price or not self.formula:
            return self.price_per_unit

        try:
            from ventilation_company.formula_engine import calculate_price

            price = calculate_price(
                self, self.formula, metal_price_per_m2 or self.metal_price_per_m2
            )
            self.price_per_unit = round(price, 2)
            return self.price_per_unit
        except Exception:
            return self.price_per_unit

    def record_price_change(self, old_price: float) -> None:
        """Записує зміну ціни в історію."""
        self.price_history.append(
            PriceHistoryEntry(
                datetime.now().strftime("%d.%m.%Y %H:%M"), old_price, self.price_per_unit
            )
        )
        if len(self.price_history) > 10:
            self.price_history = self.price_history[-10:]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "date_added": self.date_added,
            "name": self.name,
            "price_per_unit": self.price_per_unit,
            "quantity": self.quantity,
            "length": self.length,
            "width": self.width,
            "height": self.height,
            "diameter": self.diameter,
            "material": self.material,
            "thickness": self.thickness,
            "category": self.category,
            "notes": self.notes,
            "price_history": [h.to_dict() for h in self.price_history],
            "formula": self.formula,
            "auto_price": self.auto_price,
            "metal_price_per_m2": self.metal_price_per_m2,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Product":
        history = [PriceHistoryEntry.from_dict(h) for h in data.get("price_history", [])]
        return cls(
            product_id=data.get("id", ""),
            date_added=data.get("date_added", ""),
            name=data.get("name", ""),
            price_per_unit=data.get("price_per_unit", 0.0),
            quantity=data.get("quantity", 1.0),
            length=data.get("length", 0.0),
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
            diameter=data.get("diameter", 0.0),
            material=data.get("material", ""),
            thickness=data.get("thickness", 0.0),
            category=data.get("category", "Інше"),
            notes=data.get("notes", ""),
            price_history=history,
            formula=data.get("formula", ""),
            auto_price=data.get("auto_price", False),
            metal_price_per_m2=data.get("metal_price_per_m2", 0.0),
        )

    def __str__(self) -> str:
        mode = "🔧 авто" if self.auto_price else "✋ ручна"
        return f"{self.name} ({self.category}) — {self.price_per_unit:.2f} грн/шт [{mode}]"

    def __repr__(self) -> str:
        return f"Product({self.name!r}, {self.price_per_unit!r}, formula={self.formula!r})"
