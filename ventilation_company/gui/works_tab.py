#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Вкладка "Роботи"."""

import tkinter as tk
from tkinter import ttk, messagebox

from .base_tab import BaseTab
from ventilation_company.database import execute_query
from ventilation_company.project_builder.project import ProjectService
from ventilation_company.config import WORKS


class WorksTab(BaseTab):
    def setup_ui(self):
        c = self.colors
        self._init_works_db()

        outer = tk.Frame(self, bg=c["bg"])
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

        tk.Label(scroll_frame, text="КАТАЛОГ РОБІТ", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 18, "bold")).pack(pady=10)

        btn_frame = tk.Frame(scroll_frame, bg=c["bg"])
        btn_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Button(btn_frame, text="➕ Додати", bg="#27ae60", fg="white",
                  font=("Arial", 10), cursor="hand2",
                  command=self.add_work_dialog).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="✏️ Редагувати", bg="#f39c12", fg="white",
                  font=("Arial", 10), cursor="hand2",
                  command=self.edit_work_dialog).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑 Видалити", bg="#e74c3c", fg="white",
                  font=("Arial", 10), cursor="hand2",
                  command=self.delete_work).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🔄 Оновити", bg=c["accent"], fg="white",
                  font=("Arial", 10), cursor="hand2",
                  command=self.load_works_data).pack(side=tk.LEFT, padx=5)

        columns = ("ID", "Назва", "Ціна", "Одиниця", "Опис")
        self.works_tree = ttk.Treeview(scroll_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.works_tree.heading(col, text=col)
        self.works_tree.column("ID", width=50, anchor="center")
        self.works_tree.column("Назва", width=250)
        self.works_tree.column("Ціна", width=100, anchor="center")
        self.works_tree.column("Одиниця", width=90, anchor="center")
        self.works_tree.column("Опис", width=300)

        w_vsb = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL, command=self.works_tree.yview)
        self.works_tree.configure(yscrollcommand=w_vsb.set)
        self.works_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0), pady=5)
        w_vsb.pack(side=tk.LEFT, fill=tk.Y, pady=5)

        self.load_works_data()

        sep = tk.Frame(scroll_frame, bg="#bbb", height=2)
        sep.pack(fill=tk.X, padx=20, pady=8)

        add_frame = tk.LabelFrame(scroll_frame, text="Додати роботу до проекту", bg=c["bg"],
                                   fg=c["fg"], font=("Arial", 11, "bold"))
        add_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(add_frame, text="Проект:", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        projects = ProjectService.list_all()
        self._work_project_list = projects
        proj_values = [str(p[0]) + ": " + str(p[2]) for p in projects]
        self.work_project_combo = ttk.Combobox(add_frame, values=proj_values,
                                                font=("Arial", 10), width=35, state="readonly")
        self.work_project_combo.pack(side=tk.LEFT, padx=5)
        if proj_values:
            self.work_project_combo.current(0)
        self.work_project_combo.bind("<<ComboboxSelected>>", self.on_work_project_selected)

        tk.Label(add_frame, text="Робота:", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=(15, 5))
        self.work_var_catalog = tk.StringVar()
        self.work_combo_catalog = ttk.Combobox(add_frame, textvariable=self.work_var_catalog,
                                                 font=("Arial", 10), width=28, state="readonly")
        self.work_combo_catalog.pack(side=tk.LEFT)

        tk.Label(add_frame, text="Кількість:", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=(15, 5))
        self.work_qty_entry = tk.Entry(add_frame, font=("Arial", 10), width=8)
        self.work_qty_entry.insert(0, "1")
        self.work_qty_entry.pack(side=tk.LEFT)

        tk.Button(add_frame, text="➕ ДОДАТИ ДО ПРОЕКТУ", bg="#27ae60", fg="white",
                  font=("Arial", 10, "bold"), cursor="hand2",
                  command=self.add_work_to_project).pack(side=tk.LEFT, padx=20)

        proj_frame = tk.LabelFrame(scroll_frame, text="Роботи у проекті", bg=c["bg"],
                                    fg=c["fg"], font=("Arial", 11, "bold"))
        proj_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        pw_btn = tk.Frame(proj_frame, bg=c["bg"])
        pw_btn.pack(fill=tk.X, pady=3)
        tk.Button(pw_btn, text="✏️ Змінити кількість", bg="#f39c12", fg="white",
                  font=("Arial", 9), cursor="hand2",
                  command=self.edit_project_work_qty).pack(side=tk.LEFT, padx=5)
        tk.Button(pw_btn, text="🗑 Видалити", bg="#e74c3c", fg="white",
                  font=("Arial", 9), cursor="hand2",
                  command=self.delete_project_work).pack(side=tk.LEFT, padx=5)
        tk.Button(pw_btn, text="🔄 Оновити", bg=c["accent"], fg="white",
                  font=("Arial", 9), cursor="hand2",
                  command=lambda: self.load_project_works(self.current_work_project_id)).pack(side=tk.LEFT, padx=5)

        pw_cols = ("ID", "Назва", "Кількість", "Одиниця", "Ціна за од.", "Сума")
        self.proj_works_tree = ttk.Treeview(proj_frame, columns=pw_cols, show="headings", height=6)
        for col in pw_cols:
            self.proj_works_tree.heading(col, text=col)
        self.proj_works_tree.column("ID", width=50, anchor="center")
        self.proj_works_tree.column("Назва", width=250)
        self.proj_works_tree.column("Кількість", width=80, anchor="center")
        self.proj_works_tree.column("Одиниця", width=80, anchor="center")
        self.proj_works_tree.column("Ціна за од.", width=100, anchor="center")
        self.proj_works_tree.column("Сума", width=100, anchor="center")

        pw_vsb = ttk.Scrollbar(proj_frame, orient=tk.VERTICAL, command=self.proj_works_tree.yview)
        self.proj_works_tree.configure(yscrollcommand=pw_vsb.set)
        self.proj_works_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        pw_vsb.pack(side=tk.LEFT, fill=tk.Y, pady=5)

        self.current_work_project_id = None
        if proj_values:
            self.current_work_project_id = int(proj_values[0].split(":")[0])
            self.load_project_works(self.current_work_project_id)

    def _init_works_db(self):
        """Створює таблицю робіт у БД та заповнює її з WORKS якщо порожня."""
        try:
            execute_query("""
                CREATE TABLE IF NOT EXISTS works_catalog (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    price REAL NOT NULL,
                    unit TEXT NOT NULL,
                    description TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)
            count = execute_query("SELECT COUNT(*) FROM works_catalog WHERE is_active=1", fetch_one=True)[0]
            if count == 0:
                for name, data in WORKS.items():
                    price = data.get("ціна_за_м2", data.get("ціна_за_шт", data.get("ціна_за_систему", 0)))
                    unit = data.get("одиниця", "шт")
                    execute_query(
                        "INSERT OR IGNORE INTO works_catalog (name, price, unit, description) VALUES (?,?,?,?)",
                        (name, price, unit, "")
                    )
        except Exception as e:
            print("[works_db] init error:", e)

    def load_works_data(self):
        for row in self.works_tree.get_children():
            self.works_tree.delete(row)
        try:
            rows = execute_query("SELECT * FROM works_catalog WHERE is_active=1 ORDER BY name")
            for r in rows:
                self.works_tree.insert("", tk.END, values=(r[0], r[1], "{:.2f}".format(r[2]), r[3], r[4] or ""))
            names = [r[1] for r in rows]
            self.work_combo_catalog["values"] = names
            if names:
                self.work_combo_catalog.current(0)
        except Exception as e:
            messagebox.showerror("Помилка", "Не вдалося завантажити роботи: " + str(e))

    def load_project_works(self, pid):
        for row in self.proj_works_tree.get_children():
            self.proj_works_tree.delete(row)
        try:
            rows = execute_query(
                "SELECT id, work_name, quantity, unit, unit_price, total_price FROM project_works WHERE project_id=? ORDER BY id",
                (pid,)
            )
            for r in rows:
                self.proj_works_tree.insert("", tk.END, values=(r[0], r[1], r[2], r[3], "{:.2f}".format(r[4]), "{:.2f}".format(r[5])))
        except Exception as e:
            print("[load_project_works] error:", e)

    def on_work_project_selected(self, event=None):
        val = self.work_project_combo.get()
        if not val:
            return
        pid = int(val.split(":")[0])
        self.current_work_project_id = pid
        self.load_project_works(pid)

    def add_work_to_project(self):
        val = self.work_project_combo.get()
        if not val:
            messagebox.showwarning("Увага", "Оберіть проект!")
            return
        pid = int(val.split(":")[0])
        project = ProjectService.load_from_db(pid)
        if not project:
            messagebox.showerror("Помилка", "Проект не знайдено!")
            return
        work_name = self.work_var_catalog.get()
        if not work_name:
            messagebox.showwarning("Увага", "Оберіть роботу!")
            return
        try:
            qty = float(self.work_qty_entry.get().replace(",", ".") or 1)
        except ValueError:
            messagebox.showwarning("Увага", "Кількість має бути числом!")
            return
        row = execute_query("SELECT price, unit FROM works_catalog WHERE name=? AND is_active=1",
                           (work_name,), fetch_one=True)
        if not row:
            messagebox.showerror("Помилка", "Роботу не знайдено в каталозі!")
            return
        price, unit = row[0], row[1]
        project.add_work(work_name, qty, unit, price)
        project.update_in_db()
        self.load_project_works(pid)
        messagebox.showinfo("Успіх", 'Роботу "' + work_name + '" додано до проекту ' + str(project.project_number))

    def edit_project_work_qty(self):
        selected = self.proj_works_tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть роботу проекту для редагування!")
            return
        pw_id = self.proj_works_tree.item(selected[0], "values")[0]
        old_qty = self.proj_works_tree.item(selected[0], "values")[2]
        old_price = self.proj_works_tree.item(selected[0], "values")[4]

        c = self.colors
        dialog = tk.Toplevel(self.root)
        dialog.title("Змінити кількість")
        dialog.geometry("300x150")
        dialog.configure(bg=c["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Нова кількість:", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 11)).pack(pady=(15, 5))
        qty_entry = tk.Entry(dialog, font=("Arial", 11), width=12)
        qty_entry.insert(0, str(old_qty))
        qty_entry.pack()

        def save():
            try:
                new_qty = float(qty_entry.get().replace(",", "."))
            except ValueError:
                messagebox.showwarning("Увага", "Кількість має бути числом!")
                return
            new_total = new_qty * float(old_price)
            execute_query("UPDATE project_works SET quantity=?, total_price=? WHERE id=?",
                         (new_qty, new_total, pw_id))
            self.load_project_works(self.current_work_project_id)
            dialog.destroy()
            messagebox.showinfo("Успіх", "Кількість оновлено!")

        tk.Button(dialog, text="Зберегти", bg="#27ae60", fg="white",
                  font=("Arial", 11, "bold"), command=save).pack(pady=15)

    def delete_project_work(self):
        selected = self.proj_works_tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть роботу для видалення!")
            return
        pw_id = self.proj_works_tree.item(selected[0], "values")[0]
        pw_name = self.proj_works_tree.item(selected[0], "values")[1]
        if not messagebox.askyesno("Підтвердження", 'Видалити "' + pw_name + '" з проекту?'):
            return
        try:
            execute_query("DELETE FROM project_works WHERE id=?", (pw_id,))
            self.load_project_works(self.current_work_project_id)
            messagebox.showinfo("Успіх", 'Роботу "' + pw_name + '" видалено з проекту!')
        except Exception as e:
            messagebox.showerror("Помилка", str(e))

    def delete_work(self):
        selected = self.works_tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть роботу для видалення!")
            return
        work_id = self.works_tree.item(selected[0], "values")[0]
        work_name = self.works_tree.item(selected[0], "values")[1]
        if not messagebox.askyesno("Підтвердження", 'Видалити роботу "' + work_name + '"?'):
            return
        try:
            execute_query("UPDATE works_catalog SET is_active=0 WHERE id=?", (work_id,))
            self.load_works_data()
            messagebox.showinfo("Успіх", 'Роботу "' + work_name + '" видалено!')
        except Exception as e:
            messagebox.showerror("Помилка", str(e))

    def edit_work_dialog(self):
        selected = self.works_tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть роботу для редагування!")
            return
        work_id = self.works_tree.item(selected[0], "values")[0]
        row = execute_query("SELECT * FROM works_catalog WHERE id=?", (work_id,), fetch_one=True)
        if not row:
            messagebox.showerror("Помилка", "Роботу не знайдено!")
            return
        c = self.colors
        dialog = tk.Toplevel(self.root)
        dialog.title("Редагувати роботу")
        dialog.geometry("450x300")
        dialog.configure(bg=c["bg"])
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text="Назва роботи:", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 11)).pack(anchor="w", padx=20, pady=(20, 5))
        name_entry = tk.Entry(dialog, font=("Arial", 11), width=40)
        name_entry.insert(0, row[1])
        name_entry.pack(fill="x", padx=20)
        rowf = tk.Frame(dialog, bg=c["bg"])
        rowf.pack(fill="x", padx=20, pady=10)
        tk.Label(rowf, text="Ціна:", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 11)).pack(side=tk.LEFT)
        price_entry = tk.Entry(rowf, font=("Arial", 11), width=12)
        price_entry.insert(0, str(row[2]))
        price_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(rowf, text="Одиниця:", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 11)).pack(side=tk.LEFT, padx=(15, 5))
        unit_entry = tk.Entry(rowf, font=("Arial", 11), width=12)
        unit_entry.insert(0, row[3])
        unit_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(dialog, text="Опис:", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 11)).pack(anchor="w", padx=20, pady=(10, 5))
        desc_entry = tk.Entry(dialog, font=("Arial", 11), width=40)
        desc_entry.insert(0, row[4] or "")
        desc_entry.pack(fill="x", padx=20)
        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Увага", "Введіть назву роботи!")
                return
            try:
                price = float(price_entry.get().replace(",", "."))
            except ValueError:
                messagebox.showwarning("Увага", "Ціна має бути числом!")
                return
            unit = unit_entry.get().strip() or "шт"
            try:
                execute_query(
                    "UPDATE works_catalog SET name=?, price=?, unit=?, description=? WHERE id=?",
                    (name, price, unit, desc_entry.get().strip(), work_id)
                )
                self.load_works_data()
                dialog.destroy()
                messagebox.showinfo("Успіх", 'Роботу "' + name + '" оновлено!')
            except Exception as e:
                messagebox.showerror("Помилка", str(e))
        tk.Button(dialog, text="Зберегти", bg="#27ae60", fg="white",
                  font=("Arial", 12, "bold"), command=save).pack(pady=20)

    def add_work_dialog(self):
        c = self.colors
        dialog = tk.Toplevel(self.root)
        dialog.title("Додати роботу")
        dialog.geometry("450x300")
        dialog.configure(bg=c["bg"])
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text="Назва роботи:", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 11)).pack(anchor="w", padx=20, pady=(20, 5))
        name_entry = tk.Entry(dialog, font=("Arial", 11), width=40)
        name_entry.pack(fill="x", padx=20)
        row = tk.Frame(dialog, bg=c["bg"])
        row.pack(fill="x", padx=20, pady=10)
        tk.Label(row, text="Ціна:", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 11)).pack(side=tk.LEFT)
        price_entry = tk.Entry(row, font=("Arial", 11), width=12)
        price_entry.insert(0, "0")
        price_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(row, text="Одиниця:", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 11)).pack(side=tk.LEFT, padx=(15, 5))
        unit_entry = tk.Entry(row, font=("Arial", 11), width=12)
        unit_entry.insert(0, "шт")
        unit_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(dialog, text="Опис (необовязково):", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 11)).pack(anchor="w", padx=20, pady=(10, 5))
        desc_entry = tk.Entry(dialog, font=("Arial", 11), width=40)
        desc_entry.pack(fill="x", padx=20)
        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Увага", "Введіть назву роботи!")
                return
            try:
                price = float(price_entry.get().replace(",", "."))
            except ValueError:
                messagebox.showwarning("Увага", "Ціна має бути числом!")
                return
            unit = unit_entry.get().strip() or "шт"
            try:
                execute_query(
                    "INSERT INTO works_catalog (name, price, unit, description) VALUES (?,?,?,?)",
                    (name, price, unit, desc_entry.get().strip())
                )
                self.load_works_data()
                dialog.destroy()
                messagebox.showinfo("Успіх", 'Роботу "' + name + '" додано!')
            except Exception as e:
                messagebox.showerror("Помилка", str(e))
        tk.Button(dialog, text="Зберегти", bg="#27ae60", fg="white",
                  font=("Arial", 12, "bold"), command=save).pack(pady=20)
