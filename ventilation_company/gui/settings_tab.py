"""Вкладка "💰 Ціноутворення" для GUI.

Налаштування:
  • Ціни на метал (за типом і товщиною)
  • Амортизація обладнання (%)
  • Інші витрати (електроенергія, зарплата, оренда, транспорт)
  • Каталог продукції з формулами розрахунку
  • Додавання / редагування / видалення продукції
"""

import contextlib
import json
import os
import tkinter as tk
from tkinter import messagebox, ttk

SETTINGS_FILE = "data/pricing_settings.json"

DEFAULT_MATERIAL_PRICES = {
    "оцинкована сталь": {
        "0.5": 52.0,
        "0.7": 55.0,
        "0.9": 60.0,
        "1.0": 65.0,
        "1.2": 72.0,
        "1.5": 85.0,
        "2.0": 110.0,
    },
    "нержавіюча сталь": {
        "0.5": 170.0,
        "0.7": 180.0,
        "0.9": 195.0,
        "1.0": 210.0,
        "1.2": 240.0,
        "1.5": 290.0,
        "2.0": 380.0,
    },
    "алюміній": {
        "0.5": 110.0,
        "0.7": 120.0,
        "0.9": 130.0,
        "1.0": 140.0,
        "1.2": 160.0,
        "1.5": 190.0,
        "2.0": 250.0,
    },
}

DEFAULT_OVERHEAD = {
    "electricity_per_kg": 2.5,  # грн/кг — електроенергія
    "labor_per_hour": 150.0,  # грн/год — зарплата
    "rent_per_month": 15000.0,  # грн/міс — оренда
    "transport_per_project": 500.0,  # грн/проєкт — транспорт
    "waste_percent": 8.0,  # % відходів металу
}

DEFAULT_DEPRECIATION = {
    "guillotine_percent": 5.0,  # % амортизації гільйотини
    "bending_percent": 4.0,  # % амортизації листогиба
    "welding_percent": 3.0,  # % амортизації зварки
    "plasma_percent": 6.0,  # % амортизації плазми
}

DEFAULT_PRODUCTS = [
    {
        "name": "Повітропровід прямокутний",
        "formula": "metal_area * thickness * material_price * 1.15",
        "labor_hours": 0.15,
        "description": "Прямокутний канал — розгортка + згин",
    },
    {
        "name": "Повітропровід круглий",
        "formula": "metal_area * thickness * material_price * 1.20",
        "labor_hours": 0.20,
        "description": "Спірально-навивна труба",
    },
    {
        "name": "Фланець прямокутний",
        "formula": "metal_area * thickness * material_price * 1.30 + bolt_count * 2.5",
        "labor_hours": 0.25,
        "description": "Розкрій + свердління отворів",
    },
    {
        "name": "Фланець круглий",
        "formula": "metal_area * thickness * material_price * 1.30 + bolt_count * 2.5",
        "labor_hours": 0.25,
        "description": "Токарка + свердління",
    },
    {
        "name": "Трійник прямокутний",
        "formula": "metal_area * thickness * material_price * 1.50",
        "labor_hours": 0.80,
        "description": "Розкрій + врізка + згин",
    },
    {
        "name": "Трійник круглий",
        "formula": "metal_area * thickness * material_price * 1.55",
        "labor_hours": 0.90,
        "description": "Врізка в трубу + зварка",
    },
    {
        "name": "Перехід прямокутний",
        "formula": "metal_area * thickness * material_price * 1.40",
        "labor_hours": 0.60,
        "description": "Трапецієподібна розгортка",
    },
    {
        "name": "Перехід круглий",
        "formula": "metal_area * thickness * material_price * 1.45",
        "labor_hours": 0.70,
        "description": "Конусна розгортка",
    },
    {
        "name": "Відвід прямокутний",
        "formula": "metal_area * thickness * material_price * 1.60",
        "labor_hours": 1.00,
        "description": "Сегментне коліно",
    },
    {
        "name": "Відвід круглий",
        "formula": "metal_area * thickness * material_price * 1.65",
        "labor_hours": 1.10,
        "description": "Гнуте коліно",
    },
    {
        "name": "Заглушка прямокутна",
        "formula": "metal_area * thickness * material_price * 1.25",
        "labor_hours": 0.20,
        "description": "Дно + фальци",
    },
    {
        "name": "Заглушка кругла",
        "formula": "metal_area * thickness * material_price * 1.25",
        "labor_hours": 0.20,
        "description": "Витиск + фальци",
    },
    {
        "name": "Гнучка вставка",
        "formula": "metal_area * 35.0 + 25.0",
        "labor_hours": 0.10,
        "description": "Тканина + обжим",
    },
]


class PricingSettings:
    """Менеджер налаштувань ціноутворення."""

    def __init__(self, filepath=SETTINGS_FILE):
        self.filepath = filepath
        self.material_prices = {}
        self.overhead = {}
        self.depreciation = {}
        self.products = []
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, encoding="utf-8") as f:
                data = json.load(f)
            self.material_prices = data.get("material_prices", DEFAULT_MATERIAL_PRICES)
            self.overhead = data.get("overhead", DEFAULT_OVERHEAD)
            self.depreciation = data.get("depreciation", DEFAULT_DEPRECIATION)
            self.products = data.get("products", DEFAULT_PRODUCTS)
        else:
            self.material_prices = DEFAULT_MATERIAL_PRICES.copy()
            self.overhead = DEFAULT_OVERHEAD.copy()
            self.depreciation = DEFAULT_DEPRECIATION.copy()
            self.products = [p.copy() for p in DEFAULT_PRODUCTS]
            self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "material_prices": self.material_prices,
                    "overhead": self.overhead,
                    "depreciation": self.depreciation,
                    "products": self.products,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    def get_material_price(self, material, thickness):
        """Отримати ціну металу за типом і товщиною."""
        mat = self.material_prices.get(material, {})
        return mat.get(str(thickness), 55.0)

    def calculate_product_price(self, product_data):
        """Розрахувати ціну виробу за формулою."""
        # product_data: dict з metal_area, thickness, material, weight, quantity...
        material = product_data.get("material", "оцинкована сталь")
        thickness = product_data.get("thickness", 0.7)
        metal_area = product_data.get("metal_area", 0)
        weight = product_data.get("weight", 0)
        quantity = product_data.get("quantity", 1)

        material_price = self.get_material_price(material, thickness)

        # Знаходимо формулу для типу виробу
        ptype = product_data.get("type", "")
        formula = "metal_area * thickness * material_price * 1.15"
        labor_hours = 0.15
        for p in self.products:
            if p["name"] in ptype:
                formula = p.get("formula", formula)
                labor_hours = p.get("labor_hours", 0.15)
                break

        # Безпечне обчислення формули
        try:
            price = eval(
                formula,
                {"__builtins__": {}},
                {
                    "metal_area": metal_area,
                    "thickness": thickness,
                    "material_price": material_price,
                    "weight": weight,
                    "quantity": quantity,
                },
            )
        except Exception:
            price = metal_area * thickness * material_price * 1.15

        # Додаємо націнки
        waste_mult = 1 + (self.overhead.get("waste_percent", 8) / 100)
        price *= waste_mult

        # Витрати на працю
        labor_cost = labor_hours * self.overhead.get("labor_per_hour", 150)
        price += labor_cost

        # Амортизація (середнє)
        depr = sum(self.depreciation.values()) / len(self.depreciation) if self.depreciation else 4
        price *= 1 + depr / 100

        # Електроенергія
        elec = weight * self.overhead.get("electricity_per_kg", 2.5)
        price += elec

        return round(price, 2)


class SettingsTab:
    """Вкладка налаштувань ціноутворення."""

    def __init__(self, parent: ttk.Notebook):
        self.frame = ttk.Frame(parent)
        parent.add(self.frame, text="💰 Ціноутворення")

        self.settings = PricingSettings()
        self._build_ui()
        self._refresh_all()

    def _build_ui(self):
        # Верхня панель з кнопками
        top = ttk.Frame(self.frame, padding=5)
        top.pack(fill=tk.X)
        ttk.Label(top, text="💰 Налаштування ціноутворення", font=("Arial", 14, "bold")).pack(
            side=tk.LEFT
        )
        ttk.Button(top, text="💾 Зберегти налаштування", command=self._save_settings).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(top, text="🔄 Скинути за замовчуванням", command=self._reset_defaults).pack(
            side=tk.RIGHT, padx=5
        )

        # Notebook для під-вкладок
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ── Вкладка 1: Ціни на метал ──────────────────────────────
        self.metal_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.metal_frame, text="🛠️ Ціни на метал")
        self._build_metal_tab()

        # ── Вкладка 2: Витрати та амортизація ─────────────────────
        self.costs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.costs_frame, text="📊 Витрати та амортизація")
        self._build_costs_tab()

        # ── Вкладка 3: Каталог продукції ──────────────────────────
        self.catalog_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.catalog_frame, text="📦 Каталог продукції")
        self._build_catalog_tab()

    # ── ЦІНИ НА МЕТАЛ ────────────────────────────────────────────

    def _build_metal_tab(self):
        ttk.Label(self.metal_frame, text="Ціни на метал (грн/кг)", font=("Arial", 11, "bold")).pack(
            pady=5
        )

        # Таблиця: рядки — матеріали, стовпці — товщини
        frame = ttk.Frame(self.metal_frame)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        thicknesses = ["0.5", "0.7", "0.9", "1.0", "1.2", "1.5", "2.0"]
        materials = ["оцинкована сталь", "нержавіюча сталь", "алюміній"]

        # Заголовки
        ttk.Label(frame, text="Матеріал / Товщина", font=("Arial", 9, "bold")).grid(
            row=0, column=0, padx=5, pady=3
        )
        for j, th in enumerate(thicknesses):
            ttk.Label(frame, text=f"{th} мм", font=("Arial", 9, "bold")).grid(
                row=0, column=j + 1, padx=5, pady=3
            )

        self.metal_entries = {}
        for i, mat in enumerate(materials):
            ttk.Label(frame, text=mat).grid(row=i + 1, column=0, padx=5, pady=3, sticky=tk.W)
            for j, th in enumerate(thicknesses):
                var = tk.StringVar()
                ent = ttk.Entry(frame, textvariable=var, width=10)
                ent.grid(row=i + 1, column=j + 1, padx=3, pady=3)
                self.metal_entries[(mat, th)] = var

    # ── ВИТРАТИ ТА АМОРТИЗАЦІЯ ───────────────────────────────────

    def _build_costs_tab(self):
        left = ttk.LabelFrame(self.costs_frame, text="Постійні витрати", padding=10)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.cost_vars = {}
        cost_fields = [
            ("electricity_per_kg", "Електроенергія (грн/кг металу):", "2.5"),
            ("labor_per_hour", "Зарплата (грн/год):", "150.0"),
            ("rent_per_month", "Оренда (грн/міс):", "15000.0"),
            ("transport_per_project", "Транспорт (грн/проєкт):", "500.0"),
            ("waste_percent", "Відходи металу (%):", "8.0"),
        ]

        for i, (key, label, default) in enumerate(cost_fields):
            ttk.Label(left, text=label).grid(row=i, column=0, sticky=tk.W, pady=3)
            var = tk.StringVar(value=default)
            ttk.Entry(left, textvariable=var, width=12).grid(row=i, column=1, padx=5, pady=3)
            self.cost_vars[key] = var

        right = ttk.LabelFrame(self.costs_frame, text="Амортизація обладнання (%)", padding=10)
        right.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.depr_vars = {}
        depr_fields = [
            ("guillotine_percent", "Гільйотина:", "5.0"),
            ("bending_percent", "Листогиб:", "4.0"),
            ("welding_percent", "Зварка:", "3.0"),
            ("plasma_percent", "Плазма:", "6.0"),
        ]

        for i, (key, label, default) in enumerate(depr_fields):
            ttk.Label(right, text=label).grid(row=i, column=0, sticky=tk.W, pady=3)
            var = tk.StringVar(value=default)
            ttk.Entry(right, textvariable=var, width=12).grid(row=i, column=1, padx=5, pady=3)
            self.depr_vars[key] = var

        # Пояснення
        info = ttk.Label(
            self.costs_frame,
            text="💡 Формула ціни:\n"
            "  (метал × товщина × ціна × коефіцієнт) × (1 + відходи%)\n"
            "  + зарплата × години + електроенергія × вага\n"
            "  × (1 + середня амортизація%)",
            foreground="#555",
            justify=tk.LEFT,
            font=("Consolas", 9),
        )
        info.pack(side=tk.BOTTOM, pady=10, padx=10, anchor=tk.W)

    # ── КАТАЛОГ ПРОДУКЦІЇ ───────────────────────────────────────

    def _build_catalog_tab(self):
        ctrl = ttk.Frame(self.catalog_frame)
        ctrl.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(ctrl, text="➕ Додати продукцію", command=self._add_product_dialog).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(ctrl, text="✏️ Редагувати", command=self._edit_product_dialog).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(ctrl, text="🗑️ Видалити", command=self._delete_product).pack(side=tk.LEFT, padx=2)

        columns = ("name", "formula", "labor", "description")
        self.catalog_tree = ttk.Treeview(
            self.catalog_frame, columns=columns, show="headings", height=18
        )
        self.catalog_tree.heading("name", text="Назва виробу")
        self.catalog_tree.heading("formula", text="Формула розрахунку")
        self.catalog_tree.heading("labor", text="Години")
        self.catalog_tree.heading("description", text="Опис")
        self.catalog_tree.column("name", width=200)
        self.catalog_tree.column("formula", width=300)
        self.catalog_tree.column("labor", width=60)
        self.catalog_tree.column("description", width=300)

        scrollbar = ttk.Scrollbar(
            self.catalog_frame, orient=tk.VERTICAL, command=self.catalog_tree.yview
        )
        self.catalog_tree.configure(yscrollcommand=scrollbar.set)
        self.catalog_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        self.catalog_tree.bind("<Double-1>", lambda e: self._edit_product_dialog())

    def _add_product_dialog(self):
        self._product_dialog(None)

    def _edit_product_dialog(self):
        selected = self.catalog_tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть продукцію для редагування.")
            return
        idx = self.catalog_tree.index(selected[0])
        self._product_dialog(idx)

    def _product_dialog(self, idx):
        dialog = tk.Toplevel(self.frame)
        dialog.title("Продукція" if idx is None else "Редагувати продукцію")
        dialog.geometry("500x350")
        dialog.transient(self.frame)
        dialog.grab_set()

        product = self.settings.products[idx] if idx is not None else {}

        ttk.Label(dialog, text="Назва виробу:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        name_var = tk.StringVar(value=product.get("name", ""))
        ttk.Entry(dialog, textvariable=name_var, width=40).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Формула розрахунку:").grid(
            row=1, column=0, sticky=tk.W, padx=10, pady=5
        )
        formula_var = tk.StringVar(
            value=product.get("formula", "metal_area * thickness * material_price * 1.15")
        )
        ttk.Entry(dialog, textvariable=formula_var, width=40).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Години роботи:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        labor_var = tk.StringVar(value=str(product.get("labor_hours", 0.15)))
        ttk.Entry(dialog, textvariable=labor_var, width=10).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=5
        )

        ttk.Label(dialog, text="Опис:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        desc_var = tk.StringVar(value=product.get("description", ""))
        ttk.Entry(dialog, textvariable=desc_var, width=40).grid(row=3, column=1, padx=5, pady=5)

        # Довідка по змінним
        help_text = (
            "Доступні змінні у формулі:\n"
            "  metal_area — площа металу (м²)\n"
            "  thickness — товщина (мм)\n"
            "  material_price — ціна металу (грн/кг)\n"
            "  weight — вага (кг)\n"
            "  quantity — кількість"
        )
        ttk.Label(dialog, text=help_text, foreground="#2E7D32", justify=tk.LEFT).grid(
            row=4, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W
        )

        def save():
            new_product = {
                "name": name_var.get(),
                "formula": formula_var.get(),
                "labor_hours": float(labor_var.get()),
                "description": desc_var.get(),
            }
            if idx is None:
                self.settings.products.append(new_product)
            else:
                self.settings.products[idx] = new_product
            self._refresh_catalog()
            dialog.destroy()

        ttk.Button(dialog, text="Зберегти", command=save).grid(
            row=5, column=0, columnspan=2, pady=15
        )

    def _delete_product(self):
        selected = self.catalog_tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть продукцію для видалення.")
            return
        if messagebox.askyesno("Підтвердження", "Видалити обрану продукцію?"):
            idx = self.catalog_tree.index(selected[0])
            del self.settings.products[idx]
            self._refresh_catalog()

    def _refresh_all(self):
        # Ціни на метал
        for (mat, th), var in self.metal_entries.items():
            price = self.settings.material_prices.get(mat, {}).get(th, 0)
            var.set(str(price))

        # Витрати
        for key, var in self.cost_vars.items():
            var.set(str(self.settings.overhead.get(key, 0)))

        # Амортизація
        for key, var in self.depr_vars.items():
            var.set(str(self.settings.depreciation.get(key, 0)))

        # Каталог
        self._refresh_catalog()

    def _refresh_catalog(self):
        for item in self.catalog_tree.get_children():
            self.catalog_tree.delete(item)
        for p in self.settings.products:
            self.catalog_tree.insert(
                "",
                tk.END,
                values=(p["name"], p["formula"], p.get("labor_hours", 0), p.get("description", "")),
            )

    def _save_settings(self):
        # Зберігаємо ціни на метал
        for (mat, th), var in self.metal_entries.items():
            if mat not in self.settings.material_prices:
                self.settings.material_prices[mat] = {}
            with contextlib.suppress(ValueError):
                self.settings.material_prices[mat][th] = float(var.get())

        # Зберігаємо витрати
        for key, var in self.cost_vars.items():
            with contextlib.suppress(ValueError):
                self.settings.overhead[key] = float(var.get())

        # Зберігаємо амортизацію
        for key, var in self.depr_vars.items():
            with contextlib.suppress(ValueError):
                self.settings.depreciation[key] = float(var.get())

        self.settings.save()
        messagebox.showinfo("Успіх", "Налаштування збережено!")

    def _reset_defaults(self):
        if messagebox.askyesno("Підтвердження", "Скинути всі налаштування до замовчування?"):
            self.settings.material_prices = DEFAULT_MATERIAL_PRICES.copy()
            self.settings.overhead = DEFAULT_OVERHEAD.copy()
            self.settings.depreciation = DEFAULT_DEPRECIATION.copy()
            self.settings.products = [p.copy() for p in DEFAULT_PRODUCTS]
            self._refresh_all()
            self.settings.save()
