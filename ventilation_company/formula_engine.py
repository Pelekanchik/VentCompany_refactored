"""Безпечний обчислювач формул для ціноутворення.

Підтримує математичні операції та змінні виробу.
Всі обчислення в sandbox-режимі (без доступу до системи).
"""

import ast
import math
import operator

# Дозволені оператори
_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

# Дозволені функції
_ALLOWED_FUNCS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
    "ceil": math.ceil,
    "floor": math.floor,
    "round": round,
    "abs": abs,
    "min": min,
    "max": max,
}

# Змінні з підказками (для UI)
VARIABLE_HELP = {
    "length": {
        "label": "Довжина (L)",
        "unit": "мм",
        "description": "Довжина виробу вздовж осі",
        "example": "1000",
    },
    "width": {
        "label": "Ширина (W)",
        "unit": "мм",
        "description": "Ширина перерізу (прямокутник) або діаметр (круг)",
        "example": "400",
    },
    "height": {
        "label": "Висота (H)",
        "unit": "мм",
        "description": "Висота перерізу (прямокутник)",
        "example": "200",
    },
    "diameter": {
        "label": "Діаметр (Ø)",
        "unit": "мм",
        "description": "Діаметр круглого виробу",
        "example": "125",
    },
    "thickness": {
        "label": "Товщина (T)",
        "unit": "мм",
        "description": "Товщина металу",
        "example": "0.7",
    },
    "quantity": {
        "label": "Кількість (Q)",
        "unit": "шт",
        "description": "Кількість одиниць виробу",
        "example": "5",
    },
    "metal_price": {
        "label": "Ціна металу",
        "unit": "грн/м²",
        "description": "Вартість металу за 1 м² (залежить від матеріалу та товщини)",
        "example": "302.50",
    },
    "perimeter_mm": {
        "label": "Периметр",
        "unit": "мм",
        "description": "Периметр перерізу: 2×(W+H) для прямокутника, π×Ø для круга",
        "example": "1200",
    },
    "cross_area_mm2": {
        "label": "Площа перерізу",
        "unit": "мм²",
        "description": "Площа поперечного перерізу: W×H або π×Ø²/4",
        "example": "80000",
    },
    "surface_m2": {
        "label": "Площа поверхні",
        "unit": "м²",
        "description": "Розгорнута площа поверхні (периметр × довжину / 1 000 000)",
        "example": "1.2",
    },
    "volume_m3": {
        "label": "Об'єм металу",
        "unit": "м³",
        "description": "Об'єм металу (площа × товщину / 1 000 000)",
        "example": "0.00084",
    },
    "weight_kg": {
        "label": "Вага",
        "unit": "кг",
        "description": "Вага виробу (об'єм × густину, густина оцинкованої сталі ≈ 7850 кг/м³)",
        "example": "6.59",
    },
}


def get_variable_value(var_name: str, product) -> float:
    """Отримує значення змінної з об'єкта Product.

    Автоматично конвертує мм у метри де потрібно.
    """
    # Базові поля з Product (в мм)
    if var_name == "length":
        return float(product.length) if product.length else 0.0
    if var_name == "width":
        return float(product.width) if product.width else 0.0
    if var_name == "height":
        return float(product.height) if product.height else 0.0
    if var_name == "diameter":
        return float(product.diameter) if product.diameter else 0.0
    if var_name == "thickness":
        return float(product.thickness) if product.thickness else 0.0
    if var_name == "quantity":
        return float(product.quantity) if product.quantity else 1.0

    # Обчислювані значення
    if var_name == "perimeter_mm":
        if product.diameter > 0:
            return math.pi * product.diameter
        if product.width > 0 and product.height > 0:
            return 2 * (product.width + product.height)
        return 0.0

    if var_name == "cross_area_mm2":
        if product.diameter > 0:
            return math.pi * (product.diameter / 2) ** 2
        if product.width > 0 and product.height > 0:
            return product.width * product.height
        return 0.0

    if var_name == "surface_m2":
        if product.diameter > 0 and product.length > 0:
            return (math.pi * product.diameter * product.length) / 1_000_000
        if product.width > 0 and product.height > 0 and product.length > 0:
            return (2 * (product.width + product.height) * product.length) / 1_000_000
        return 0.0

    if var_name == "volume_m3":
        surf = get_variable_value("surface_m2", product)
        thick = product.thickness / 1000.0 if product.thickness else 0.0
        return surf * thick

    if var_name == "weight_kg":
        vol = get_variable_value("volume_m3", product)
        # Густина за замовчуванням — оцинкована сталь
        density = 7850  # кг/м³
        if product.material and "нержав" in product.material.lower():
            density = 7900
        elif product.material and "алюм" in product.material.lower():
            density = 2700
        return vol * density

    if var_name == "metal_price":
        # Повертаємо 0, має бути передано ззовні
        return 0.0

    raise NameError(f"Невідома змінна: '{var_name}'")


def evaluate_formula(formula: str, variables: dict[str, float]) -> float:
    """Безпечно обчислює формулу.

    Args:
        formula: рядок формули, наприклад "surface_m2 * metal_price * 1.15"
        variables: словник змінних {ім'я: значення}

    Returns:
        результат обчислення (float)

    Raises:
        ValueError: якщо формула некоректна або містить заборонені елементи
    """
    if not formula or not formula.strip():
        return 0.0

    formula = formula.strip()

    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Синтаксична помилка у формулі: {e}") from e

    def _eval(node):
        if isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        if isinstance(node, ast.Constant):  # Python >= 3.8
            if isinstance(node.value, int | float):
                return node.value
            raise ValueError(f"Недопустимий тип константи: {type(node.value).__name__}")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _ALLOWED_OPS:
                raise ValueError(f"Недопустимий оператор: {op_type.__name__}")
            left = _eval(node.left)
            right = _eval(node.right)
            return _ALLOWED_OPS[op_type](left, right)

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _ALLOWED_OPS:
                raise ValueError(f"Недопустимий унарний оператор: {op_type.__name__}")
            operand = _eval(node.operand)
            return _ALLOWED_OPS[op_type](operand)

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Недопустимий виклик функції")
            func_name = node.func.id
            if func_name not in _ALLOWED_FUNCS:
                raise ValueError(f"Недопустима функція: '{func_name}'")
            args = [_eval(arg) for arg in node.args]
            return _ALLOWED_FUNCS[func_name](*args)

        if isinstance(node, ast.Name):
            name = node.id
            if name in _ALLOWED_FUNCS and name not in variables:
                return _ALLOWED_FUNCS[name]
            if name not in variables:
                raise NameError(f"Невідома змінна: '{name}'")
            return variables[name]

        if isinstance(node, ast.Expression):
            return _eval(node.body)

        raise ValueError(f"Недопустимий елемент: {type(node).__name__}")

    result = _eval(tree)

    if not isinstance(result, int | float):
        raise ValueError("Результат формули має бути числом")

    return float(result)


def calculate_price(product, formula: str, metal_price_per_m2: float = 0.0) -> float:
    """Розраховує ціну виробу за формулою.

    Args:
        product: об'єкт Product
        formula: рядок формули
        metal_price_per_m2: ціна металу за м² (грн/м²)

    Returns:
        ціна за 1 штуку (грн)
    """
    variables = {}
    from contextlib import suppress

    variables = {}
    for var_name in VARIABLE_HELP:
        with suppress(NameError):
            variables[var_name] = get_variable_value(var_name, product)

    variables["metal_price"] = float(metal_price_per_m2)

    return evaluate_formula(formula, variables)


def validate_formula(formula: str) -> tuple[bool, str]:
    """Перевіряє формулу на коректність.

    Returns:
        (is_valid, error_message)
    """
    if not formula or not formula.strip():
        return False, "Формула не може бути порожньою"

    test_vars = {name: 1.0 for name in VARIABLE_HELP}
    test_vars["metal_price"] = 100.0

    try:
        result = evaluate_formula(formula, test_vars)
        if result < 0:
            return False, f"Результат формули від'ємний: {result}"
        return True, f"✅ Формула коректна. Тестовий результат: {result:.4f}"
    except Exception as e:
        return False, f"❌ Помилка: {str(e)}"


def get_formula_examples() -> list[dict]:
    """Повертає приклади формул з поясненнями."""
    return [
        {
            "name": "Листова деталь (площа × ціна × коеф.)",
            "formula": "surface_m2 * metal_price * 1.15",
            "description": "Площа поверхні × ціна металу за м² × коефіцієнт витрат (15%)",
        },
        {
            "name": "Прямокутний повітропровід",
            "formula": "(width + height) * 2 * length / 1000000 * metal_price * 1.1",
            "description": "Периметр × довжину → м² × ціна × коефіцієнт",
        },
        {
            "name": "Круглий повітропровід",
            "formula": "pi * diameter * length / 1000000 * metal_price * 1.1",
            "description": "π × діаметр × довжину → м² × ціна × коефіцієнт",
        },
        {
            "name": "Фланець (площа диска × ціна)",
            "formula": "pi * (diameter / 2) ** 2 / 1000000 * metal_price * 1.2",
            "description": "Площа круга × ціна × коеф. 1.2 (на отвори під болти)",
        },
        {
            "name": "Заглушка (площа + борти)",
            "formula": "(width * height + 2 * (width + height) * thickness) / 1000000 * metal_price * 1.1",
            "description": "Площа дна + боки × ціна × коефіцієнт",
        },
        {
            "name": "Відвід (дуга × периметр)",
            "formula": "perimeter_mm * length / 1000000 * metal_price * 1.25",
            "description": "Периметр × довжину дуги × ціна × коеф. 1.25 (гнуття)",
        },
        {
            "name": "Вага × ціна за кг (стара система)",
            "formula": "weight_kg * metal_price / (thickness / 1000 * 7850)",
            "description": "Вага × ціна за кг. Увага: metal_price тут має бути ціною за КГ, не за м²!",
        },
    ]
