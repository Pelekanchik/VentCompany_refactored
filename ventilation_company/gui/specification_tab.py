"""Вкладка "Специфікація" для GUI.
Формує, відображає та експортує специфікацію виробів проєкту.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ventilation_company.auto_specification import SpecBuilder


class SpecificationTab:
    """Вкладка специфікації."""

    EXPORT_FORMATS = {
        "JSON (.json)": "json",
        "CSV (.csv)": "csv",
        "Текст (.txt)": "txt",
        "HTML (.html)": "html",
    }

    def __init__(self, parent: ttk.Notebook, get_products_callback):
        self.frame = ttk.Frame(parent)
        parent.add(self.frame, text="📋 Специфікація")

        self.get_products = get_products_callback
        self.current_spec = None

        self._build_ui()

    def _build_ui(self):
        ctrl_frame = ttk.Frame(self.frame)
        ctrl_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(ctrl_frame, text="Назва проєкту:").pack(side=tk.LEFT, padx=2)
        self.project_name_var = tk.StringVar(value="Новий проєкт")
        ttk.Entry(ctrl_frame, textvariable=self.project_name_var, width=30).pack(
            side=tk.LEFT, padx=2
        )

        ttk.Button(ctrl_frame, text="🔄 Сформувати", command=self._generate).pack(
            side=tk.LEFT, padx=10
        )

        ttk.Label(ctrl_frame, text="Експорт:").pack(side=tk.LEFT, padx=(20, 2))
        self.export_var = tk.StringVar(value="JSON (.json)")
        ttk.Combobox(
            ctrl_frame,
            textvariable=self.export_var,
            values=list(self.EXPORT_FORMATS.keys()),
            state="readonly",
            width=15,
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="💾 Зберегти", command=self._export).pack(side=tk.LEFT, padx=2)

        # Основна таблиця
        columns = (
            "pos",
            "name",
            "type",
            "dims",
            "material",
            "thick",
            "qty",
            "w_unit",
            "w_total",
            "a_unit",
            "a_total",
            "price",
        )
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", height=18)

        headers = {
            "pos": "№",
            "name": "Найменування",
            "type": "Тип",
            "dims": "Розміри",
            "material": "Матеріал",
            "thick": "Товщ.",
            "qty": "К-ть",
            "w_unit": "Вага 1 шт",
            "w_total": "Вага заг.",
            "a_unit": "Площа 1 шт",
            "a_total": "Площа заг.",
            "price": "Ціна, грн",
        }
        widths = {
            "pos": 30,
            "name": 180,
            "type": 140,
            "dims": 100,
            "material": 100,
            "thick": 50,
            "qty": 40,
            "w_unit": 70,
            "w_total": 70,
            "a_unit": 70,
            "a_total": 70,
            "price": 80,
        }

        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor=tk.CENTER if col != "name" else tk.W)

        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # Підсумки — компактно в один рядок
        self.summary_frame = ttk.LabelFrame(self.frame, text="📊 Підсумки", padding=5)
        self.summary_frame.pack(fill=tk.X, padx=5, pady=2, side=tk.BOTTOM)

        self.summary_labels = {}
        summary_items = [
            ("total_items", "Позицій:"),
            ("total_qty", "Кількість:"),
            ("total_weight", "Вага, кг:"),
            ("total_area", "Площа, м²:"),
            ("total_price", "Вартість, грн:"),
        ]

        for i, (key, text) in enumerate(summary_items):
            ttk.Label(self.summary_frame, text=text, font=("Arial", 9)).grid(
                row=0, column=i * 2, padx=(10 if i > 0 else 5), pady=2
            )
            lbl = ttk.Label(self.summary_frame, text="0", font=("Arial", 10, "bold"))
            lbl.grid(row=0, column=i * 2 + 1, padx=2, pady=2)
            self.summary_labels[key] = lbl

    def _generate(self):
        products = self.get_products()
        if not products:
            messagebox.showwarning(
                "Увага", "Список виробів порожній. Додайте вироби у вкладці 'Вироби'."
            )
            return

        builder = SpecBuilder(project_name=self.project_name_var.get())
        builder.set_material_price("оцинкована сталь", 55.0)
        builder.set_material_price("нержавіюча сталь", 180.0)
        builder.set_material_price("алюміній", 120.0)

        for p in products:
            builder.add_product(p)

        self.current_spec = builder.build()
        self._refresh_tree()
        self._update_summary()

    def _refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.current_spec:
            return

        for item in self.current_spec.items:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    item.position,
                    item.name,
                    item.product_type,
                    item.dimensions,
                    item.material,
                    item.thickness,
                    item.quantity,
                    f"{item.weight_per_unit:.3f}",
                    f"{item.weight_total:.3f}",
                    f"{item.area_per_unit:.4f}",
                    f"{item.area_total:.4f}",
                    f"{item.price_total:.2f}",
                ),
            )

    def _update_summary(self):
        if not self.current_spec:
            return

        self.summary_labels["total_items"].config(text=str(self.current_spec.total_items))
        self.summary_labels["total_qty"].config(text=str(self.current_spec.total_quantity))
        self.summary_labels["total_weight"].config(text=f"{self.current_spec.total_weight:.3f}")
        self.summary_labels["total_area"].config(text=f"{self.current_spec.total_area:.4f}")
        self.summary_labels["total_price"].config(text=f"{self.current_spec.total_price:.2f}")

    def _export(self):
        if not self.current_spec:
            messagebox.showwarning("Увага", "Спочатку сформуйте специфікацію.")
            return

        fmt_name = self.export_var.get()
        fmt = self.EXPORT_FORMATS.get(fmt_name, "json")
        ext = fmt

        filepath = filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            filetypes=[(fmt_name, f"*.{ext}")],
            initialfile=f"spec_{self.project_name_var.get().replace(' ', '_')}",
        )

        if filepath:
            try:
                content = self.current_spec.to_dict()
                if fmt == "json":
                    import json

                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(content, f, ensure_ascii=False, indent=2)
                elif fmt == "csv":
                    with open(filepath, "w", encoding="utf-8-sig") as f:
                        f.write(self.current_spec.to_csv())
                elif fmt == "txt":
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(self.current_spec.to_txt())
                elif fmt == "html":
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(self.current_spec.to_html())

                messagebox.showinfo("Успіх", f"Специфікація збережена:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося зберегти:\n{str(e)}")

    def get_specification(self):
        return self.current_spec
