#!/usr/bin/env python3
"""Вкладка \"Бухгалтерія\"."""

import tkinter as tk
from tkinter import messagebox, ttk

from ventilation_company.calculations.expenses import ExpenseTracker
from ventilation_company.calculations.pricing import PricingEngine
from ventilation_company.calculations.salary_calculator import SalaryCalculator

from .base_tab import BaseTab


class AccountingTab(BaseTab):
    def _make_scrollable(self, parent, title):
        """Створює прокручувану вкладку"""
        c = self.colors
        outer = tk.Frame(parent, bg=c["bg"])
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=c["bg"], highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        scroll_frame = tk.Frame(canvas, bg=c["bg"])
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def on_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        scroll_frame.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        return scroll_frame

    def setup_ui(self):
        c = self.colors
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=15, pady=10)

        calc_tab = tk.Frame(notebook, bg=c["bg"])
        notebook.add(calc_tab, text="  🧮 Розрахунки  ")
        calc_scroll = self._make_scrollable(calc_tab, "Розрахунки")
        self._build_calculations(calc_scroll)

        sal_tab = tk.Frame(notebook, bg=c["bg"])
        notebook.add(sal_tab, text="  💰 Зарплата  ")
        sal_scroll = self._make_scrollable(sal_tab, "Зарплата")
        self._build_salary(sal_scroll)

        exp_tab = tk.Frame(notebook, bg=c["bg"])
        notebook.add(exp_tab, text="  📉 Витрати  ")
        exp_scroll = self._make_scrollable(exp_tab, "Витрати")
        self._build_expenses(exp_scroll)

    def _build_calculations(self, parent):
        c = self.colors
        tk.Label(
            parent, text="КАЛЬКУЛЯТОР ВАРТОСТІ", bg=c["bg"], fg=c["fg"], font=("Arial", 16, "bold")
        ).pack(pady=10)
        fields = [("Базова собівартість (грн):", "cost")]
        self.calc_entries = {}
        for label, key in fields:
            row = tk.Frame(parent, bg=c["bg"])
            row.pack(fill="x", padx=50, pady=5)
            tk.Label(
                row, text=label, bg=c["bg"], fg=c["fg"], font=("Arial", 11), width=25, anchor="e"
            ).pack(side=tk.LEFT)
            widget = tk.Entry(row, font=("Arial", 11), width=20)
            widget.insert(0, "10000")
            self.calc_entries[key] = widget
            widget.pack(side=tk.LEFT, padx=5)

        self.calc_result = tk.Label(
            parent, text="", bg=c["bg"], fg=c["fg"], font=("Arial", 12), justify="left"
        )
        self.calc_result.pack(pady=20)
        tk.Button(
            parent,
            text="🧮 Розрахувати",
            bg=c["accent"],
            fg="white",
            font=("Arial", 12),
            command=self.do_calculation,
        ).pack(pady=10)

    def do_calculation(self):
        try:
            base_cost = float(self.calc_entries["cost"].get())
        except ValueError:
            messagebox.showerror("Помилка", "Введіть коректну собівартість!")
            return
        engine = PricingEngine(base_cost)
        result = engine.cost_plus_pricing()
        text = (
            f"Собівартість: {result['base_cost']:.2f} грн\n"
            f"Націнка: {result['markup_amount']:.2f} грн\n"
            f"ПДВ: {result['vat_amount']:.2f} грн\n"
            f"КІНЦЕВА ЦІНА: {result['final_price']:.2f} грн\n"
            f"Прибуток: {result['profit']:.2f} грн\n"
            f"Маржа: {result['profit_margin']:.2f}%"
        )
        self.calc_result.config(text=text)

    def _build_salary(self, parent):
        c = self.colors
        tk.Label(
            parent, text="РОЗРАХУНОК ЗАРПЛАТИ", bg=c["bg"], fg=c["fg"], font=("Arial", 16, "bold")
        ).pack(pady=10)

        row = tk.Frame(parent, bg=c["bg"])
        row.pack(fill="x", padx=50, pady=5)
        tk.Label(
            row,
            text="ПІБ працівника:",
            bg=c["bg"],
            fg=c["fg"],
            font=("Arial", 11),
            width=15,
            anchor="e",
        ).pack(side=tk.LEFT)
        self.salary_name = tk.Entry(row, font=("Arial", 11), width=30)
        self.salary_name.pack(side=tk.LEFT, padx=5)

        row = tk.Frame(parent, bg=c["bg"])
        row.pack(fill="x", padx=50, pady=5)
        tk.Label(
            row, text="Посада:", bg=c["bg"], fg=c["fg"], font=("Arial", 11), width=15, anchor="e"
        ).pack(side=tk.LEFT)
        from ventilation_company.config import POSITIONS

        self.salary_position = ttk.Combobox(
            row, values=list(POSITIONS.keys()), font=("Arial", 11), width=28, state="readonly"
        )
        self.salary_position.pack(side=tk.LEFT, padx=5)
        if POSITIONS:
            self.salary_position.current(0)

        row = tk.Frame(parent, bg=c["bg"])
        row.pack(fill="x", padx=50, pady=5)
        tk.Label(
            row,
            text="Базова ставка:",
            bg=c["bg"],
            fg=c["fg"],
            font=("Arial", 11),
            width=15,
            anchor="e",
        ).pack(side=tk.LEFT)
        self.salary_base = tk.Entry(row, font=("Arial", 11), width=15)
        self.salary_base.insert(0, "15000")
        self.salary_base.pack(side=tk.LEFT, padx=5)

        row = tk.Frame(parent, bg=c["bg"])
        row.pack(fill="x", padx=50, pady=5)
        tk.Label(
            row,
            text="Премія (%):",
            bg=c["bg"],
            fg=c["fg"],
            font=("Arial", 11),
            width=15,
            anchor="e",
        ).pack(side=tk.LEFT)
        self.salary_bonus = tk.Entry(row, font=("Arial", 11), width=15)
        self.salary_bonus.insert(0, "10")
        self.salary_bonus.pack(side=tk.LEFT, padx=5)

        self.salary_result = tk.Label(
            parent, text="", bg=c["bg"], fg=c["fg"], font=("Arial", 12), justify="left"
        )
        self.salary_result.pack(pady=20)
        tk.Button(
            parent,
            text="💰 Розрахувати",
            bg=c["accent"],
            fg="white",
            font=("Arial", 12),
            command=self.calculate_salary,
        ).pack(pady=10)

    def calculate_salary(self):
        try:
            base = float(self.salary_base.get())
            bonus = float(self.salary_bonus.get())
        except ValueError:
            messagebox.showerror("Помилка", "Введіть коректні числа!")
            return
        calc = SalaryCalculator()
        calc.add_employee(
            self.salary_name.get() or "Працівник", self.salary_position.get(), base, bonus
        )
        result = calc.calculate_payroll()
        if result["details"]:
            d = result["details"][0]
            text = (
                f"Брутто: {d['gross_salary']:.2f} грн\n"
                f"ПДФО (18%): {d['pit']:.2f} грн\n"
                f"Військовий збір (1.5%): {d['military_tax']:.2f} грн\n"
                f"ЄСВ (роботодавець): {d['esv']:.2f} грн\n"
                f"До видачі: {d['net_salary']:.2f} грн"
            )
        else:
            text = "Додайте працівника"
        self.salary_result.config(text=text)

    def _build_expenses(self, parent):
        c = self.colors
        tk.Label(parent, text="ВИТРАТИ", bg=c["bg"], fg=c["fg"], font=("Arial", 16, "bold")).pack(
            pady=10
        )
        btn_frame = tk.Frame(parent, bg=c["bg"])
        btn_frame.pack(fill=tk.X, padx=50, pady=5)
        tk.Button(
            btn_frame,
            text="➕ Додати витрату",
            bg="#27ae60",
            fg="white",
            font=("Arial", 11),
            command=self.add_expense,
        ).pack(side=tk.LEFT, padx=5)

        columns = ("Дата", "Категорія", "Сума", "Опис")
        self.expenses_tree = ttk.Treeview(parent, columns=columns, show="headings", height=12)
        for col in columns:
            self.expenses_tree.heading(col, text=col)
            self.expenses_tree.column(col, width=150)
        self.expenses_tree.pack(fill=tk.BOTH, expand=True, padx=50, pady=10)

        self.tracker = ExpenseTracker()
        self.update_expenses_display()

    def add_expense(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Нова витрата")
        dialog.geometry("400x250")
        c = self.colors
        dialog.configure(bg=c["bg"])
        entries = {}
        for label, key in [("Категорія:", "cat"), ("Сума:", "sum"), ("Опис:", "desc")]:
            row = tk.Frame(dialog, bg=c["bg"])
            row.pack(fill="x", padx=20, pady=5)
            tk.Label(
                row, text=label, bg=c["bg"], fg=c["fg"], font=("Arial", 11), width=12, anchor="e"
            ).pack(side=tk.LEFT)
            e = tk.Entry(row, font=("Arial", 11))
            e.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
            entries[key] = e

        def save():
            try:
                amount = float(entries["sum"].get())
            except ValueError:
                messagebox.showerror("Помилка", "Сума має бути числом")
                return
            self.tracker.add_expense(entries["cat"].get(), amount, entries["desc"].get())
            dialog.destroy()
            self.update_expenses_display()

        tk.Button(
            dialog, text="💾 Зберегти", bg="#27ae60", fg="white", font=("Arial", 11), command=save
        ).pack(pady=15)

    def update_expenses_display(self):
        for item in self.expenses_tree.get_children():
            self.expenses_tree.delete(item)
        for exp in self.tracker.expenses:
            self.expenses_tree.insert(
                "",
                tk.END,
                values=(
                    exp.get("date", "")[:10],
                    exp.get("category", ""),
                    exp.get("amount", 0),
                    exp.get("description", ""),
                ),
            )
