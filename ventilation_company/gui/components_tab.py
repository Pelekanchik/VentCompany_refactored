#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Вкладка \"Вироби\" — калькулятор + типи виробів."""

import tkinter as tk
from tkinter import ttk, messagebox

from .base_tab import BaseTab
from ventilation_company.project_builder.project import ProjectService
from ventilation_company.detail_calculator import DetailCalculatorFrame


class ComponentsTab(BaseTab):
    def setup_ui(self):
        c = self.colors

        # === ВИБІР ПРОЕКТУ ===
        proj_bar = tk.Frame(self, bg=c["bg"])
        proj_bar.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Label(proj_bar, text="📁 Проект:", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        projects = ProjectService.list_all()
        self._comp_project_list = projects
        proj_values = [str(p[0]) + ": " + str(p[2]) for p in projects]

        self.comp_project_var = tk.StringVar()
        self.comp_project_combo = ttk.Combobox(proj_bar, values=proj_values,
                                                width=45, state="readonly", font=("Arial", 11))
        self.comp_project_combo.pack(side=tk.LEFT, padx=10)
        if proj_values:
            self.comp_project_combo.current(0)

        # Кнопка синхронізації з розкроєм
        tk.Button(proj_bar, text="📤 Передати на розкрій", bg="#e67e22", fg="white",
                  font=("Arial", 10, "bold"), cursor="hand2",
                  command=self.sync_to_camduct).pack(side=tk.LEFT, padx=(20, 5))

        # Кнопки калькулятора
        tk.Button(proj_bar, text="🧮 Розрахувати", bg="#27ae60", fg="white",
                  font=("Arial", 10, "bold"), cursor="hand2",
                  command=lambda: self.detail_calculator.calculate_all() if hasattr(self, 'detail_calculator') else None).pack(side=tk.LEFT, padx=5)
        tk.Button(proj_bar, text="📊 Excel", bg="#3498db", fg="white",
                  font=("Arial", 10, "bold"), cursor="hand2",
                  command=lambda: self.detail_calculator.export_current_xlsx() if hasattr(self, 'detail_calculator') else None).pack(side=tk.LEFT, padx=5)
        tk.Button(proj_bar, text="🖨️ Друк", bg="#9b59b6", fg="white",
                  font=("Arial", 10, "bold"), cursor="hand2",
                  command=lambda: self.detail_calculator.print_current() if hasattr(self, 'detail_calculator') else None).pack(side=tk.LEFT, padx=5)

        def on_proj_select(event=None):
            val = self.comp_project_combo.get()
            if val and hasattr(self, 'detail_calculator'):
                pid = int(val.split(":")[0])
                self.detail_calculator.set_project_id(pid)
                proj = next((p for p in projects if p[0] == pid), None)
                if proj and hasattr(self.detail_calculator, 'calc_client'):
                    self.detail_calculator.calc_client.delete(0, tk.END)
                    self.detail_calculator.calc_client.insert(0, proj[3] if proj[3] else "")

        self.comp_project_combo.bind("<<ComboboxSelected>>", on_proj_select)

        # === Калькулятор БЕЗ Canvas (напряму у фреймі) ===
        self.detail_calculator = DetailCalculatorFrame(self, colors=self.colors)
        self.detail_calculator.pack(fill=tk.BOTH, expand=True)

        on_proj_select()

    def sync_to_camduct(self):
        """Передає деталі з калькулятора виробів у розкрій листа"""
        if not hasattr(self, 'detail_calculator') or not self.detail_calculator.calc_items:
            messagebox.showwarning("Увага", "Спочатку додайте вироби у вкладці 'Вироби'!")
            return
        camduct_tab = self.app.tabs.get("camduct")
        if not camduct_tab or not hasattr(camduct_tab, 'camduct_editor') or camduct_tab.camduct_editor is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте вкладку 'Розкрій листа' хоча б раз.")
            return
        count = camduct_tab.camduct_editor.import_calc_items(self.detail_calculator.calc_items, clear_existing=True)
        if count > 0:
            messagebox.showinfo("Готово", "Передано " + str(count) + " позицій на розкрій!\n\nПерейдіть на вкладку 'Розкрій листа' та натисніть 'РОЗКРИТИ'.")
        else:
            messagebox.showwarning("Увага", "Не вдалося передати деталі. Перевірте типи виробів.")
