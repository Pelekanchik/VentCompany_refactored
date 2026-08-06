"""
Бібліотека стандартних виробів для вентиляційних систем.
Фланці, трійники, переходи, відводи, заглушки — готові параметричні блоки
з автоматичним розрахунком площі металу та ваги.
"""

import math
from dataclasses import dataclass, field
from enum import Enum


class MaterialType(Enum):
    GALVANIZED = "оцинкована сталь"
    STAINLESS = "нержавіюча сталь"
    ALUMINUM = "алюміній"


class Thickness(Enum):
    T0_5 = 0.5
    T0_7 = 0.7
    T0_9 = 0.9
    T1_0 = 1.0
    T1_2 = 1.2
    T1_5 = 1.5
    T2_0 = 2.0


# Щільності матеріалів, кг/м³
DENSITY = {
    MaterialType.GALVANIZED: 7850,
    MaterialType.STAINLESS: 7900,
    MaterialType.ALUMINUM: 2700,
}


@dataclass
class StandardProduct:
    """Базовий клас стандартного виробу."""

    name: str
    product_type: str = ""
    width: float = 0.0  # мм
    height: float = 0.0  # мм (або діаметр для круглих)
    length: float = 0.0  # мм
    thickness: Thickness = field(default=Thickness.T0_7)
    material: MaterialType = field(default=MaterialType.GALVANIZED)
    quantity: int = 1
    notes: str = ""

    # Автоматично розраховується
    metal_area: float = field(init=False)  # м² розгорнутої площі
    weight: float = field(init=False)  # кг

    def __post_init__(self):
        self.metal_area = self.calculate_metal_area()
        self.weight = self.calculate_weight()

    def calculate_metal_area(self) -> float:
        """Розрахунок розгорнутої площі металу (м²). Перевизначається в підкласах."""
        return 0.0

    def calculate_weight(self) -> float:
        """Розрахунок ваги виробу (кг)."""
        volume = self.metal_area * (self.thickness.value / 1000)  # м³
        return volume * DENSITY[self.material]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.product_type,
            "width": self.width,
            "height": self.height,
            "length": self.length,
            "thickness": self.thickness.value,
            "material": self.material.value,
            "quantity": self.quantity,
            "metal_area_m2": round(self.metal_area, 4),
            "weight_kg": round(self.weight, 4),
            "notes": self.notes,
        }


# =========================================================
# ФЛАНЦІ
# =========================================================


@dataclass
class RectFlange(StandardProduct):
    """Прямокутний фланець з отворами під болти."""

    bolt_diameter: float = 10  # мм, діаметр отвору
    bolt_spacing: float = 100  # мм, крок отворів
    flange_border: float = 30  # мм, ширина полки фланця

    def __post_init__(self):
        self.product_type = "фланець прямокутний"
        super().__post_init__()

    def calculate_metal_area(self) -> float:
        # Периметр фланця = периметр повітропроводу + полки з 4 сторін
        w = self.width / 1000
        h = self.height / 1000
        border = self.flange_border / 1000

        # Площа фланця = (W + 2*border) * (H + 2*border)
        flange_w = w + 2 * border
        flange_h = h + 2 * border
        area = flange_w * flange_h

        # Мінус площа отворів під болти
        bolts_x = int((self.width + 2 * self.flange_border) / self.bolt_spacing) + 1
        bolts_y = int((self.height + 2 * self.flange_border) / self.bolt_spacing) + 1
        bolt_area = bolts_x * bolts_y * math.pi * (self.bolt_diameter / 2000) ** 2

        # Додатково: площа під гумовий ущільнювач (рахується окремо як комплектуюче)
        return max(0, area - bolt_area)


@dataclass
class RoundFlange(StandardProduct):
    """Круглий фланець (навісний)."""

    bolt_diameter: float = 10
    bolt_count: int = 8
    flange_width: float = 30  # мм, ширина полки

    def __post_init__(self):
        self.product_type = "фланець круглий"
        super().__post_init__()

    def calculate_metal_area(self) -> float:
        # Діаметр = height (для круглих використовуємо height як діаметр)
        d = self.height / 1000
        border = self.flange_width / 1000

        # Площа кільця = π*(R² - r²)
        R = (d / 2) + border
        r = d / 2
        area = math.pi * (R**2 - r**2)

        # Мінус отвори під болти
        bolt_area = self.bolt_count * math.pi * (self.bolt_diameter / 2000) ** 2
        return max(0, area - bolt_area)


# =========================================================
# ТРІЙНИКИ
# =========================================================


@dataclass
class RectTee(StandardProduct):
    """Прямокутний трійник (відгалуження збоку)."""

    branch_width: float = 0.0  # мм, ширина відгалуження
    branch_height: float = 0.0  # мм, висота відгалуження
    branch_length: float = 0.0  # мм, довжина відгалуження
    angle: float = 90  # градуси, кут відгалуження

    def __post_init__(self):
        self.product_type = "трійник прямокутний"
        super().__post_init__()

    def calculate_metal_area(self) -> float:
        # Основний канал
        w, h, l = self.width / 1000, self.height / 1000, self.length / 1000
        main_area = 2 * (w + h) * l

        # Відгалуження
        bw, bh, bl = self.branch_width / 1000, self.branch_height / 1000, self.branch_length / 1000
        branch_area = 2 * (bw + bh) * bl

        # Площа з'єднання (врізка) — прямокутник
        joint_area = bw * bh

        # Припуск на згин (15%)
        total = (main_area + branch_area - joint_area) * 1.15
        return total


@dataclass
class RoundTee(StandardProduct):
    """Круглий трійник."""

    branch_diameter: float = 0.0  # мм
    branch_length: float = 0.0  # мм
    angle: float = 90

    def __post_init__(self):
        self.product_type = "трійник круглий"
        super().__post_init__()

    def calculate_metal_area(self) -> float:
        d = self.height / 1000  # основний діаметр
        bd = self.branch_diameter / 1000
        l = self.length / 1000
        bl = self.branch_length / 1000

        # Основний канал
        main_area = math.pi * d * l

        # Відгалуження
        branch_area = math.pi * bd * bl

        # Врізка (площа перетину меншого)
        joint_area = math.pi * (min(d, bd) / 2) ** 2

        return (main_area + branch_area - joint_area) * 1.15


# =========================================================
# ПЕРЕХОДИ
# =========================================================


@dataclass
class RectTransition(StandardProduct):
    """Прямокутний перехід (змінення розміру)."""

    end_width: float = 0.0
    end_height: float = 0.0

    def __post_init__(self):
        self.product_type = "перехід прямокутний"
        super().__post_init__()

    def calculate_metal_area(self) -> float:
        w1, h1 = self.width / 1000, self.height / 1000
        w2, h2 = self.end_width / 1000, self.end_height / 1000
        l = self.length / 1000

        # Середній периметр
        p1 = 2 * (w1 + h1)
        p2 = 2 * (w2 + h2)
        p_avg = (p1 + p2) / 2

        # Площа бічної поверхні трапеції
        area = p_avg * l

        # Припуск на згин (10%)
        return area * 1.10


@dataclass
class RoundTransition(StandardProduct):
    """Круглий перехід (перехідник)."""

    end_diameter: float = 0.0

    def __post_init__(self):
        self.product_type = "перехід круглий"
        super().__post_init__()

    def calculate_metal_area(self) -> float:
        d1 = self.height / 1000
        d2 = self.end_diameter / 1000
        l = self.length / 1000

        # Площа бічної поверхні зрізаного конуса
        # S = π * (r1 + r2) * sqrt(l² + (r1 - r2)²)
        r1, r2 = d1 / 2, d2 / 2
        slant = math.sqrt(l**2 + (r1 - r2) ** 2)
        area = math.pi * (r1 + r2) * slant

        return area * 1.10


# =========================================================
# ВІДВОДИ (КОЛІНА)
# =========================================================


@dataclass
class RectElbow(StandardProduct):
    """Прямокутне коліно (відвід)."""

    angle: float = 90  # градуси
    segments: int = 3  # кількість гнутих сегментів
    radius: float = 150  # мм, радіус згину

    def __post_init__(self):
        self.product_type = "відвід прямокутний"
        super().__post_init__()

    def calculate_metal_area(self) -> float:
        w, h = self.width / 1000, self.height / 1000
        r = self.radius / 1000
        angle_rad = math.radians(self.angle)

        # Довжина дуги
        arc_length = r * angle_rad

        # Площа бічної поверхні
        area = 2 * (w + h) * arc_length

        # Припуск на згин (20% — більше через складну геометрію)
        return area * 1.20


@dataclass
class RoundElbow(StandardProduct):
    """Кругле коліно."""

    angle: float = 90
    segments: int = 3
    radius: float = 150

    def __post_init__(self):
        self.product_type = "відвід круглий"
        super().__post_init__()

    def calculate_metal_area(self) -> float:
        d = self.height / 1000
        r = self.radius / 1000
        angle_rad = math.radians(self.angle)

        arc_length = r * angle_rad
        area = math.pi * d * arc_length

        return area * 1.20


# =========================================================
# ЗАГЛУШКИ
# =========================================================


@dataclass
class RectCap(StandardProduct):
    """Прямокутна заглушка."""

    flange_border: float = 25

    def __post_init__(self):
        self.product_type = "заглушка прямокутна"
        self.length = self.flange_border  # для заглушки length = глибина загину
        super().__post_init__()

    def calculate_metal_area(self) -> float:
        w, h = self.width / 1000, self.height / 1000
        border = self.flange_border / 1000

        # Дно + 4 боковини
        bottom = w * h
        sides = 2 * (w + h) * border

        return (bottom + sides) * 1.10


@dataclass
class RoundCap(StandardProduct):
    """Кругла заглушка."""

    depth: float = 30

    def __post_init__(self):
        self.product_type = "заглушка кругла"
        self.length = self.depth
        super().__post_init__()

    def calculate_metal_area(self) -> float:
        d = self.height / 1000
        r = d / 2
        depth = self.depth / 1000

        # Дно (коло) + бічна поверхня (циліндр)
        bottom = math.pi * r**2
        side = math.pi * d * depth

        return (bottom + side) * 1.10


# =========================================================
# СКРУБЕР / З'ЄДНУВАЧ
# =========================================================


@dataclass
class FlexibleConnector(StandardProduct):
    """Гнучка вставка (тканинна, не металева — для специфікації)."""

    fabric_type: str = "поліестер"

    def __post_init__(self):
        self.product_type = "гнучка вставка"
        super().__post_init__()

    def calculate_metal_area(self) -> float:
        # Гнучка вставка не з металу, але рахуємо площу тканини
        w, h, l = self.width / 1000, self.height / 1000, self.length / 1000
        return 2 * (w + h) * l

    def calculate_weight(self) -> float:
        # Приблизна вага тканини ~0.3 кг/м²
        return self.metal_area * 0.3


# =========================================================
# ФАБРИКА ВИРОБІВ
# =========================================================


class ProductLibrary:
    """Бібліотека стандартних виробів з можливістю збереження/завантаження."""

    def __init__(self):
        self.products: list[StandardProduct] = []

    def add(self, product: StandardProduct):
        self.products.append(product)

    def get_by_type(self, product_type: str) -> list[StandardProduct]:
        return [p for p in self.products if p.product_type == product_type]

    def get_total_metal_area(self) -> float:
        return sum(p.metal_area * p.quantity for p in self.products)

    def get_total_weight(self) -> float:
        return sum(p.weight * p.quantity for p in self.products)

    def get_specification(self) -> list[dict]:
        """Повертає специфікацію з групуванням однакових виробів."""
        from collections import defaultdict

        grouped = defaultdict(lambda: {"quantity": 0, "area": 0.0, "weight": 0.0})

        for p in self.products:
            key = (p.product_type, p.width, p.height, p.length, p.thickness, p.material)
            grouped[key]["quantity"] += p.quantity
            grouped[key]["area"] += p.metal_area * p.quantity
            grouped[key]["weight"] += p.weight * p.quantity
            grouped[key]["product"] = p

        result = []
        for key, data in grouped.items():
            p = data["product"]
            result.append(
                {
                    "name": p.name,
                    "type": p.product_type,
                    "dimensions": f"{p.width}×{p.height}×{p.length}",
                    "thickness": p.thickness.value,
                    "material": p.material.value,
                    "quantity": data["quantity"],
                    "total_area_m2": round(data["area"], 4),
                    "total_weight_kg": round(data["weight"], 4),
                }
            )

        return sorted(result, key=lambda x: x["type"])

    def to_dict(self) -> list[dict]:
        return [p.to_dict() for p in self.products]

    def clear(self):
        self.products.clear()

    def __len__(self):
        return len(self.products)

    def __repr__(self):
        return f"ProductLibrary(products={len(self.products)}, total_area={self.get_total_metal_area():.3f} м²)"


# =========================================================
# ШВИДКІ ФУНКЦІЇ-БІЛДЕРИ
# =========================================================


def make_rect_duct(
    width: float,
    height: float,
    length: float,
    thickness: float = 0.7,
    material: MaterialType = MaterialType.GALVANIZED,
    quantity: int = 1,
) -> StandardProduct:
    """Швидке створення прямокутного повітропроводу."""
    thickness_enum = Thickness.T0_7
    for t in Thickness:
        if abs(t.value - thickness) < 0.01:
            thickness_enum = t
            break

    class RectDuct(StandardProduct):
        def __post_init__(self):
            self.product_type = "повітропровід прямокутний"
            super().__post_init__()

        def calculate_metal_area(self):
            w, h, l = self.width / 1000, self.height / 1000, self.length / 1000
            return 2 * (w + h) * l

    return RectDuct(
        name=f"Повітропровід {width}×{height}",
        product_type="повітропровід прямокутний",
        width=width,
        height=height,
        length=length,
        thickness=thickness_enum,
        material=material,
        quantity=quantity,
    )


def make_round_duct(
    diameter: float,
    length: float,
    thickness: float = 0.7,
    material: MaterialType = MaterialType.GALVANIZED,
    quantity: int = 1,
) -> StandardProduct:
    """Швидке створення круглого повітропроводу."""
    thickness_enum = Thickness.T0_7
    for t in Thickness:
        if abs(t.value - thickness) < 0.01:
            thickness_enum = t
            break

    class RoundDuct(StandardProduct):
        def __post_init__(self):
            self.product_type = "повітропровід круглий"
            super().__post_init__()

        def calculate_metal_area(self):
            d, l = self.height / 1000, self.length / 1000
            return math.pi * d * l

    return RoundDuct(
        name=f"Повітропровід Ø{diameter}",
        product_type="повітропровід круглий",
        width=diameter,
        height=diameter,
        length=length,
        thickness=thickness_enum,
        material=material,
        quantity=quantity,
    )
