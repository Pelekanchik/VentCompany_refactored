#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Вкладка \"Проекти\"."""

import tkinter as tk
from tkinter import ttk, messagebox

from .base_tab import BaseTab
from ventilation_company.database import execute_query
from ventilation_company.models.project import Project
from ventilation_company.project_builder.project import ProjectService
from ventilation_company.project_builder.export import ProjectExporter
from ventilation_company.calculations.cost_calculator import CostCalculator
from ventilation_company.config import VENTILATION_TYPES, DB_PATH


class ProjectsTab(BaseTab):
    def setup_ui(self):
        c = self.colors

        btn_frame = tk.Frame(self, bg=c["bg"])
        btn_frame.pack(fill=tk.X, pady=10)

        tk.Button(btn_frame, text="➕ Новий проект", bg="#27ae60", fg="white",
                  font=("Arial", 11), command=self.show_new_project_dialog).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🔄 Оновити", bg=c["accent"], fg="white",
                  font=("Arial", 11), command=self.refresh).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="✏️ Редагувати", bg=c["accent"], fg="white",
                  font=("Arial", 11), command=self.edit_selected_project).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Видалити", bg="#e74c3c", fg="white",
                  font=("Arial", 11), command=self.delete_selected_project).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🧮 Розрахунок", bg="#27ae60", fg="white",
                  font=("Arial", 11), command=self.calculate_selected_project).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📤 Експорт", bg="#9b59b6", fg="white",
                  font=("Arial", 11), command=self.export_selected_project).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📐 Креслення", bg="#1abc9c", fg="white",
                  font=("Arial", 11), command=self.open_project_drawing).pack(side=tk.LEFT, padx=5)

        columns = ("ID", "Номер", "Назва", "Замовник", "Тип", "Витрата", "Тиск", "Дата")
        self.projects_tree = ttk.Treeview(self, columns=columns, show="headings", height=20)
        for col in columns:
            self.projects_tree.heading(col, text=col)
            self.projects_tree.column(col, width=120, anchor="center")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.projects_tree.yview)
        self.projects_tree.configure(yscrollcommand=scrollbar.set)

        self.projects_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh()

    def refresh(self):
        for item in self.projects_tree.get_children():
            self.projects_tree.delete(item)
        try:
            projects = ProjectService.list_all()
            for proj in projects:
                self.projects_tree.insert("", tk.END, values=proj)
            self.set_status(f"Завантажено проектів: {len(projects)}")
        except Exception as e:
            self.show_error("Помилка", f"Не вдалося завантажити проекти: {e}")

    def get_selected_project_id(self):
        selected = self.projects_tree.selection()
        if not selected:
            self.show_message("Увага", "Оберіть проект!")
            return None
        return self.projects_tree.item(selected[0])["values"][0]

    def edit_selected_project(self):
        pid = self.get_selected_project_id()
        if pid:
            self.show_edit_project_dialog(pid)

    def delete_selected_project(self):
        pid = self.get_selected_project_id()
        if pid and self.ask_confirmation("Підтвердження", "Видалити проект?"):
            execute_query("DELETE FROM projects WHERE id = ?", (pid,))
            self.refresh()
            self.show_message("Успіх", "Проект видалено")

    def calculate_selected_project(self):
        pid = self.get_selected_project_id()
        if not pid:
            return
        project = ProjectService.load_from_db(pid)
        if not project:
            return
        calc = CostCalculator(project)
        result = calc.calculate()
        calc.save_calculation()
        msg = (f"РОЗРАХУНОК ВАРТОСТІ:\n"
               f"Матеріали: {result['materials_cost']:.2f} грн\n"
               f"Комплектуючі: {result['components_cost']:.2f} грн\n"
               f"Роботи: {result['works_cost']:.2f} грн\n"
               f"Собівартість: {result['total_cost']:.2f} грн\n"
               f"Націнка ({result['markup_percentage']}%): {result['markup_amount']:.2f} грн\n"
               f"ПДВ ({result['vat_rate']}%): {result['vat_amount']:.2f} грн\n"
               f"КІНЦЕВА ЦІНА: {result['final_price']:.2f} грн\n"
               f"Прибуток: {result['profit']:.2f} грн\n"
               f"Рентабельність: {result['profit_margin_percent']:.2f}%")
        self.show_message("Розрахунок", msg)

    def export_selected_project(self):
        pid = self.get_selected_project_id()
        if not pid:
            return
        project = ProjectService.load_from_db(pid)
        if not project:
            return
        exporter = ProjectExporter(project)
        files = exporter.export_all()
        self.show_message("Експорт", f"Проект експортовано!\nФайлів: {len(files)}")

    def open_project_drawing(self):
        pid = self.get_selected_project_id()
        if not pid:
            return
        project = ProjectService.load_from_db(pid)
        if not project:
            self.show_error("Помилка", "Проект не знайдено!")
            return
        try:
            from ventilation_company.drawing_editor import launch_editor
            launch_editor(DB_PATH, pid, project.name)
        except Exception as e:
            self.show_error("Помилка", f"Не вдалося відкрити редактор: {e}")

    def show_new_project_dialog(self):
        c = self.colors
        dialog = tk.Toplevel(self.root)
        dialog.title("Створення нового проекту")
        dialog.geometry("700x500")
        dialog.configure(bg=c["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="СТВОРЕННЯ НОВОГО ПРОЕКТУ", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 18, "bold")).pack(pady=15)

        fields = [
            ("Назва проекту*:", "name", ""),
            ("Замовник:", "client", ""),
            ("Адреса об'єкту:", "address", ""),
            ("Витрата повітря (м³/год):", "airflow", "0"),
            ("Тиск (Па):", "pressure", "0"),
        ]
        entries = {}
        for label, key, default in fields:
            row = tk.Frame(dialog, bg=c["bg"])
            row.pack(fill="x", padx=40, pady=5)
            tk.Label(row, text=label, bg=c["bg"], fg=c["fg"], font=("Arial", 11), width=22, anchor="e").pack(side=tk.LEFT)
            e = tk.Entry(row, font=("Arial", 11), width=40)
            e.insert(0, default)
            e.pack(side=tk.LEFT, padx=5)
            entries[key] = e

        row = tk.Frame(dialog, bg=c["bg"])
        row.pack(fill="x", padx=40, pady=5)
        tk.Label(row, text="Тип вентиляції:", bg=c["bg"], fg=c["fg"], font=("Arial", 11), width=22, anchor="e").pack(side=tk.LEFT)
        type_var = tk.StringVar(value="Припливна")
        ttk.Combobox(row, textvariable=type_var, values=VENTILATION_TYPES, font=("Arial", 11), width=38, state="readonly").pack(side=tk.LEFT, padx=5)

        def create_project():
            name = entries["name"].get().strip()
            if not name:
                messagebox.showwarning("Увага", "Назва проекту обов'язкова!")
                return
            try:
                airflow = self._parse_float(entries["airflow"].get(), "Витрата повітря")
                pressure = self._parse_float(entries["pressure"].get(), "Тиск")
            except ValueError as e:
                messagebox.showerror("Помилка", str(e))
                return
            project = Project(
                name=name, client=entries["client"].get().strip(),
                address=entries["address"].get().strip(),
                ventilation_type=type_var.get(), air_flow=airflow, pressure=pressure
            )
            ProjectService.save_to_db(project)
            dialog.destroy()
            self.refresh()
            self.show_message("Успіх", "Проект створено!")

        tk.Button(dialog, text="💾 Створити проект", bg="#27ae60", fg="white",
                  font=("Arial", 12, "bold"), command=create_project).pack(pady=20)

    def show_edit_project_dialog(self, pid):
        project = ProjectService.load_from_db(pid)
        if not project:
            return
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Редагування проекту {project.project_number}")
        dialog.geometry("980x520")
        dialog.configure(bg=self.colors["bg"])
        dialog.minsize(650, 450)
        c = self.colors
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        tab_main = tk.Frame(notebook, bg=c["bg"])
        notebook.add(tab_main, text="Основне")

        def make_field(parent, label_text, default, width=40):
            row = tk.Frame(parent, bg=c["bg"])
            row.pack(fill="x", pady=2, padx=5)
            tk.Label(row, text=label_text, bg=c["bg"], fg=c["fg"], font=("Arial", 10), width=20, anchor="e").pack(side=tk.LEFT)
            e = tk.Entry(row, font=("Arial", 10), width=width)
            e.insert(0, default)
            e.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
            return e

        name_entry = make_field(tab_main, "Назва:", project.name)
        client_entry = make_field(tab_main, "Замовник:", project.client)
        address_entry = make_field(tab_main, "Адреса:", project.address)

        row = tk.Frame(tab_main, bg=c["bg"])
        row.pack(fill="x", pady=2, padx=5)
        tk.Label(row, text="Тип вентиляції:", bg=c["bg"], fg=c["fg"], font=("Arial", 10), width=20, anchor="e").pack(side=tk.LEFT)
        type_var = tk.StringVar(value=project.ventilation_type)
        ttk.Combobox(row, textvariable=type_var, values=VENTILATION_TYPES, font=("Arial", 10), width=38, state="readonly").pack(side=tk.LEFT, padx=5, fill="x", expand=True)

        row = tk.Frame(tab_main, bg=c["bg"])
        row.pack(fill="x", pady=2, padx=5)
        tk.Label(row, text="Витрата (м³/год):", bg=c["bg"], fg=c["fg"], font=("Arial", 10), width=20, anchor="e").pack(side=tk.LEFT)
        airflow_entry = tk.Entry(row, font=("Arial", 10), width=12)
        airflow_entry.insert(0, str(project.air_flow))
        airflow_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(row, text="Тиск (Па):", bg=c["bg"], fg=c["fg"], font=("Arial", 10)).pack(side=tk.LEFT, padx=(20, 0))
        pressure_entry = tk.Entry(row, font=("Arial", 10), width=12)
        pressure_entry.insert(0, str(project.pressure))
        pressure_entry.pack(side=tk.LEFT, padx=5)

        def save_changes():
            try:
                new_air_flow = self._parse_float(airflow_entry.get(), "Витрата повітря")
                new_pressure = self._parse_float(pressure_entry.get(), "Тиск")
            except ValueError as e:
                messagebox.showerror("Помилка вводу", str(e))
                return
            project.name = name_entry.get()
            project.client = client_entry.get()
            project.address = address_entry.get()
            project.ventilation_type = type_var.get()
            project.air_flow = new_air_flow
            project.pressure = new_pressure
            ProjectService.save_to_db(project)
            dialog.destroy()
            self.refresh()
            self.show_message("Успіх", "Зміни збережено!")

        tk.Button(dialog, text="💾 Зберегти зміни", bg="#27ae60", fg="white",
                  font=("Arial", 12, "bold"), command=save_changes).pack(pady=10)
