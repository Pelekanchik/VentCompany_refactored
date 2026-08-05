#!/usr/bin/env python3
"""Вкладка \"Матеріали\"."""

import tkinter as tk
from tkinter import ttk

from ventilation_company.config import MATERIALS

from .base_tab import BaseTab


class MaterialsTab(BaseTab):
    def setup_ui(self):
        c = self.colors
        tk.Label(
            self, text="КАТАЛОГ МАТЕРІАЛІВ", bg=c["bg"], fg=c["fg"], font=("Arial", 18, "bold")
        ).pack(pady=15)

        columns = ("Назва", "Ціна за м²", "Одиниця")
        tree = ttk.Treeview(self, columns=columns, show="headings", height=20)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=300)

        for name, data in MATERIALS.items():
            price = data.get("ціна_за_м2", data.get("price", 0))
            unit = data.get("одиниця", "м²")
            tree.insert("", tk.END, values=(name, price, unit))

        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
