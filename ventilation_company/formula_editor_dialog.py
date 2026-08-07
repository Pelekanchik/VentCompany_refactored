"""Діалог редагування формули для ціноутворення.
З підказками для змінних та перевіркою формули.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from ventilation_company.formula_engine import (
    VARIABLE_HELP,
    calculate_price,
    get_formula_examples,
    validate_formula,
)


class FormulaEditorDialog(tk.Toplevel):
    """Діалог для створення та редагування формули розрахунку ціни."""

    def __init__(self, parent, product, metal_price_per_m2: float = 0.0, on_save=None):
        super().__init__(parent)
        self.title("🔧 Редактор формули ціноутворення")
        self.geometry("750x600")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.product = product
        self.metal_price_per_m2 = metal_price_per_m2
        self.on_save = on_save
        self.result_formula = None
        self.result_auto_price = False

        self._build_ui()
        self._load_current_formula()

        self.wait_visibility()
        self.focus_set()

    def _build_ui(self):
        # === Верхня панель: інформація про виріб ===
        info_frame = ttk.LabelFrame(self, text="📋 Інформація про виріб", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        dims = self.product.dimensions_str
        mat = self.product.material or "—"
        thick = f"{self.product.thickness} мм" if self.product.thickness else "—"

        ttk.Label(info_frame, text=f"Назва: {self.product.name}", font=("Arial", 10, "bold")).pack(
            anchor="w"
        )
        ttk.Label(
            info_frame, text=f"Розміри: {dims}  |  Матеріал: {mat}  |  Товщина: {thick}"
        ).pack(anchor="w")
        ttk.Label(
            info_frame,
            text=f"Ціна металу: {self.metal_price_per_m2:.2f} грн/м²",
            foreground="#2E7D32",
        ).pack(anchor="w")

        # === Ліва панель: доступні змінні ===
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        left_frame = ttk.LabelFrame(main_frame, text="📐 Доступні змінні", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        # Таблиця змінних з підказками
        var_tree = ttk.Treeview(
            left_frame, columns=("var", "label", "unit", "value"), show="headings", height=12
        )
        var_tree.heading("var", text="Змінна")
        var_tree.heading("label", text="Назва")
        var_tree.heading("unit", text="Од.")
        var_tree.heading("value", text="Значення")

        var_tree.column("var", width=100)
        var_tree.column("label", width=120)
        var_tree.column("unit", width=40)
        var_tree.column("value", width=70)

        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=var_tree.yview)
        var_tree.configure(yscrollcommand=scrollbar.set)

        var_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Заповнюємо змінні
        from ventilation_company.formula_engine import get_variable_value

        for var_name, info in VARIABLE_HELP.items():
            try:
                val = get_variable_value(var_name, self.product)
                if var_name == "metal_price":
                    val = self.metal_price_per_m2
                var_tree.insert(
                    "", tk.END, values=(var_name, info["label"], info["unit"], f"{val:.4f}")
                )
            except Exception:
                var_tree.insert("", tk.END, values=(var_name, info["label"], info["unit"], "—"))

        # Подвійний клік — вставити змінну в формулу
        var_tree.bind("<Double-1>", lambda e: self._insert_variable(var_tree))

        # Підказка при наведенні
        self.var_tree = var_tree

        # === Права панель: редактор формули ===
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Режим ціноутворення
        mode_frame = ttk.Frame(right_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(mode_frame, text="Режим:").pack(side=tk.LEFT)
        self.mode_var = tk.BooleanVar(value=False)
        ttk.Radiobutton(
            mode_frame,
            text="✋ Ручна ціна",
            variable=self.mode_var,
            value=False,
            command=self._toggle_mode,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            mode_frame,
            text="🔧 Авто-формула",
            variable=self.mode_var,
            value=True,
            command=self._toggle_mode,
        ).pack(side=tk.LEFT, padx=5)

        # Поле формули
        formula_frame = ttk.LabelFrame(right_frame, text="📝 Формула розрахунку ціни", padding=5)
        formula_frame.pack(fill=tk.BOTH, expand=True)

        self.formula_text = tk.Text(formula_frame, height=4, wrap=tk.WORD, font=("Consolas", 11))
        self.formula_text.pack(fill=tk.BOTH, expand=True)

        # Підказка під формулою
        hint_text = (
            "💡 Підказка: клацніть двічі на змінну зліва, щоб вставити її. "
            "Використовуйте +, -, *, /, **, sqrt(), pi, min(), max(), round()"
        )
        ttk.Label(formula_frame, text=hint_text, foreground="#666", font=("Arial", 8)).pack(
            anchor="w", pady=(2, 0)
        )

        # Кнопки перевірки
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="✅ Перевірити формулу", command=self._validate).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="🧮 Розрахувати тестово", command=self._test_calculate).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="📋 Вставити приклад", command=self._show_examples).pack(
            side=tk.LEFT, padx=2
        )

        # Результат перевірки
        self.result_label = ttk.Label(
            right_frame, text="", font=("Arial", 9, "bold"), wraplength=400
        )
        self.result_label.pack(fill=tk.X, pady=5)

        # === Нижня панель: кнопки ===
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(bottom_frame, text="💾 Зберегти", command=self._save).pack(side=tk.RIGHT, padx=2)
        ttk.Button(bottom_frame, text="❌ Скасувати", command=self.destroy).pack(
            side=tk.RIGHT, padx=2
        )

    def _toggle_mode(self):
        """Перемикає режим редагування."""
        if self.mode_var.get():
            self.formula_text.config(state=tk.NORMAL)
        else:
            self.formula_text.config(state=tk.DISABLED)

    def _load_current_formula(self):
        """Завантажує поточну формулу виробу."""
        self.mode_var.set(self.product.auto_price)
        if self.product.formula:
            self.formula_text.insert("1.0", self.product.formula)
        self._toggle_mode()

    def _insert_variable(self, tree):
        """Вставляє вибрану змінну в поле формули."""
        selected = tree.selection()
        if not selected:
            return
        item = tree.item(selected[0])
        var_name = item["values"][0]

        self.formula_text.config(state=tk.NORMAL)
        self.formula_text.insert(tk.INSERT, var_name)
        self.formula_text.focus_set()

    def _validate(self):
        """Перевіряє формулу на коректність."""
        formula = self.formula_text.get("1.0", tk.END).strip()
        if not formula:
            self.result_label.config(text="⚠️ Формула порожня", foreground="#FF6F00")
            return

        is_valid, msg = validate_formula(formula)
        color = "#2E7D32" if is_valid else "#C62828"
        self.result_label.config(text=msg, foreground=color)

    def _test_calculate(self):
        """Тестово розраховує ціну за формулою для поточного виробу."""
        formula = self.formula_text.get("1.0", tk.END).strip()
        if not formula:
            self.result_label.config(text="⚠️ Формула порожня", foreground="#FF6F00")
            return

        try:
            price = calculate_price(self.product, formula, self.metal_price_per_m2)
            self.result_label.config(
                text=f"✅ Тестовий розрахунок: {price:.2f} грн/шт",
                foreground="#2E7D32",
            )
        except Exception as e:
            self.result_label.config(text=f"❌ Помилка: {str(e)}", foreground="#C62828")

    def _show_examples(self):
        """Показує вікно з прикладами формул."""
        examples = get_formula_examples()

        win = tk.Toplevel(self)
        win.title("📋 Приклади формул")
        win.geometry("700x400")
        win.transient(self)
        win.grab_set()

        tree = ttk.Treeview(
            win, columns=("name", "formula", "description"), show="headings", height=10
        )
        tree.heading("name", text="Назва")
        tree.heading("formula", text="Формула")
        tree.heading("description", text="Опис")
        tree.column("name", width=150)
        tree.column("formula", width=250)
        tree.column("description", width=280)

        for ex in examples:
            tree.insert("", tk.END, values=(ex["name"], ex["formula"], ex["description"]))

        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Button(
            win, text="📋 Копіювати формулу", command=lambda: self._copy_example(tree, win)
        ).pack(pady=5)
        ttk.Button(win, text="Закрити", command=win.destroy).pack(pady=5)

    def _copy_example(self, tree, win):
        """Копіює вибрану формулу в редактор."""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть приклад зі списку")
            return
        item = tree.item(selected[0])
        formula = item["values"][1]

        self.formula_text.config(state=tk.NORMAL)
        self.formula_text.delete("1.0", tk.END)
        self.formula_text.insert("1.0", formula)
        self.mode_var.set(True)
        self._toggle_mode()
        win.destroy()
        self._test_calculate()

    def _save(self):
        """Зберігає формулу та закриває діалог."""
        self.result_auto_price = self.mode_var.get()
        self.result_formula = self.formula_text.get("1.0", tk.END).strip()

        if self.result_auto_price and not self.result_formula:
            messagebox.showwarning("Увага", "Увімкнено авто-формулу, але формула порожня!")
            return

        if self.result_auto_price:
            is_valid, msg = validate_formula(self.result_formula)
            if not is_valid:
                messagebox.showerror("Помилка формули", msg)
                return

        if self.on_save:
            self.on_save(self.result_formula, self.result_auto_price)

        self.destroy()
