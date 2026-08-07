"""Вкладка "Вироби" для GUI."""

import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, messagebox, simpledialog, ttk

from ventilation_company.freecad_models import FREECAD_AVAILABLE, export_products_to_freecad
from ventilation_company.standard_products import (
    FlexibleConnector,
    MaterialType,
    ProductLibrary,
    RectCap,
    RectElbow,
    RectFlange,
    RectTee,
    RectTransition,
    RoundCap,
    RoundElbow,
    RoundFlange,
    RoundTee,
    RoundTransition,
    Thickness,
    make_rect_duct,
    make_round_duct,
)


class ProductsTab:
    """Вкладка управління виробами проєкту."""

    PRODUCT_TYPES = {
        "Повітропровід прямокутний": "rect_duct",
        "Повітропровід круглий": "round_duct",
        "Фланець прямокутний": "rect_flange",
        "Фланець круглий": "round_flange",
        "Трійник прямокутний": "rect_tee",
        "Трійник круглий": "round_tee",
        "Перехід прямокутний": "rect_transition",
        "Перехід круглий": "round_transition",
        "Відвід прямокутний": "rect_elbow",
        "Відвід круглий": "round_elbow",
        "Заглушка прямокутна": "rect_cap",
        "Заглушка кругла": "round_cap",
        "Гнучка вставка": "flexible",
    }

    MATERIALS = {
        "Оцинкована сталь": MaterialType.GALVANIZED,
        "Нержавіюча сталь": MaterialType.STAINLESS,
        "Алюміній": MaterialType.ALUMINUM,
    }

    THICKNESSES = {
        "0.5 мм": Thickness.T0_5,
        "0.7 мм": Thickness.T0_7,
        "0.9 мм": Thickness.T0_9,
        "1.0 мм": Thickness.T1_0,
        "1.2 мм": Thickness.T1_2,
        "1.5 мм": Thickness.T1_5,
        "2.0 мм": Thickness.T2_0,
    }

    HELP_TEXTS = {
        "rect_duct": (
            "📐 Прямокутний повітропровід\n"
            "Ширина × Висота = внутрішній переріз (мм)\n"
            "Довжина = розмір вздовж осі (мм)"
        ),
        "round_duct": (
            "🔵 Круглий повітропровід (труба)\n"
            "Ширина/Ø = діаметр труби (мм)\n"
            "Висота = те саме, що Ø\n"
            "Довжина = розмір вздовж осі (мм)"
        ),
        "rect_flange": (
            "⬜ Прямокутний фланець\n"
            "Ширина × Висота = під повітропровід (мм)\n"
            "Полка 30 мм додається автоматично\n"
            "Отвори під болти кроком 100 мм"
        ),
        "round_flange": (
            "🔘 Круглий фланець\n"
            "Ширина/Ø = діаметр під трубу (мм)\n"
            "Полка 30 мм, 8 отворів під болти"
        ),
        "rect_tee": (
            "┬ Прямокутний трійник\n"
            "Ш×В = основний канал (мм)\n"
            "Довжина = основного каналу\n"
            "Відстань від краю = від початку до центру відгалуження\n"
            "Відгалуження Ш×В = бічний канал\n"
            "Довжина відгалуження = бічного каналу"
        ),
        "round_tee": (
            "┬ Круглий трійник\n"
            "Ø = діаметр основної труби (мм)\n"
            "Довжина = основної труби\n"
            "Відстань від краю = від початку до центру відгалуження\n"
            "Ø відгалуження = діаметр бічної труби\n"
            "Довжина відгалуження = бічної труби"
        ),
        "rect_transition": (
            "◺ Прямокутний перехід\n"
            "Ш×В = початковий переріз (мм)\n"
            "Кінцеві Ш×В = кінцевий переріз\n"
            "Довжина = розмір переходу"
        ),
        "round_transition": (
            "◺ Круглий перехід\n"
            "Ø = початковий діаметр (мм)\n"
            "Кінцевий Ø = кінцевий діаметр\n"
            "Довжина = розмір переходу"
        ),
        "rect_elbow": (
            "⌒ Прямокутне коліно\n"
            "Ш×В = переріз (мм)\n"
            "Кут = кут згину (90°, 45°...)\n"
            "Радіус = радіус дуги згину"
        ),
        "round_elbow": (
            "⌒ Кругле коліно\n"
            "Ø = діаметр труби (мм)\n"
            "Кут = кут згину (90°, 45°...)\n"
            "Радіус = радіус дуги згину"
        ),
        "rect_cap": (
            "⊞ Прямокутна заглушка\n"
            "Ш×В = під повітропровід (мм)\n"
            "Ширина загину = глибина фальця"
        ),
        "round_cap": (
            "⊞ Кругла заглушка\n" "Ø = діаметр під трубу (мм)\n" "Глибина = висота заглушки"
        ),
        "flexible": (
            "〰 Гнучка вставка\n"
            "Ш×В = переріз (мм)\n"
            "Довжина = довжина вставки\n"
            "Тканина — компенсує вібрацію"
        ),
    }

    def __init__(self, parent: ttk.Notebook, on_products_changed: Callable | None = None):
        self.frame = ttk.Frame(parent)
        parent.add(self.frame, text="📦 Вироби")

        self.library = ProductLibrary()
        self.on_products_changed = on_products_changed

        self._build_ui()
        self._update_summary()

    def _build_ui(self):
        left_frame = ttk.LabelFrame(self.frame, text="Додати виріб", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        ttk.Label(left_frame, text="Тип:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.type_var = tk.StringVar(value="Повітропровід прямокутний")
        self.type_combo = ttk.Combobox(
            left_frame,
            textvariable=self.type_var,
            values=list(self.PRODUCT_TYPES.keys()),
            state="readonly",
            width=28,
        )
        self.type_combo.grid(row=0, column=1, pady=2)
        self.type_combo.bind("<<ComboboxSelected>>", self._on_type_changed)

        ttk.Label(left_frame, text="Ширина/Ø (мм):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.width_var = tk.StringVar(value="400")
        ttk.Entry(left_frame, textvariable=self.width_var, width=12).grid(row=1, column=1, pady=2)

        ttk.Label(left_frame, text="Висота (мм):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.height_var = tk.StringVar(value="200")
        self.height_entry = ttk.Entry(left_frame, textvariable=self.height_var, width=12)
        self.height_entry.grid(row=2, column=1, pady=2)

        ttk.Label(left_frame, text="Довжина (мм):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.length_var = tk.StringVar(value="1000")
        ttk.Entry(left_frame, textvariable=self.length_var, width=12).grid(row=3, column=1, pady=2)

        self.extra_frame = ttk.Frame(left_frame)
        self.extra_frame.grid(row=4, column=0, columnspan=2, pady=5, sticky=tk.EW)
        self.extra_widgets = []

        ttk.Label(left_frame, text="Матеріал:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.material_var = tk.StringVar(value="Оцинкована сталь")
        ttk.Combobox(
            left_frame,
            textvariable=self.material_var,
            values=list(self.MATERIALS.keys()),
            state="readonly",
            width=28,
        ).grid(row=5, column=1, pady=2)

        ttk.Label(left_frame, text="Товщина:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.thickness_var = tk.StringVar(value="0.7 мм")
        ttk.Combobox(
            left_frame,
            textvariable=self.thickness_var,
            values=list(self.THICKNESSES.keys()),
            state="readonly",
            width=28,
        ).grid(row=6, column=1, pady=2)

        ttk.Label(left_frame, text="Кількість:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.qty_var = tk.StringVar(value="1")
        ttk.Entry(left_frame, textvariable=self.qty_var, width=12).grid(row=7, column=1, pady=2)

        ttk.Button(left_frame, text="➕ Додати виріб", command=self._add_product).grid(
            row=8, column=0, columnspan=2, pady=10, sticky=tk.EW
        )

        self.help_label = ttk.Label(
            left_frame,
            text=self.HELP_TEXTS["rect_duct"],
            foreground="#2E7D32",
            wraplength=300,
            justify=tk.LEFT,
            font=("Consolas", 9),
        )
        self.help_label.grid(row=9, column=0, columnspan=2, pady=5, sticky=tk.W)

        right_frame = ttk.Frame(self.frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("type", "dimensions", "material", "thickness", "qty", "area", "weight")
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=15)

        self.tree.heading("type", text="Тип")
        self.tree.heading("dimensions", text="Розміри")
        self.tree.heading("material", text="Матеріал")
        self.tree.heading("thickness", text="Товщ.")
        self.tree.heading("qty", text="К-ть")
        self.tree.heading("area", text="Площа, м²")
        self.tree.heading("weight", text="Вага, кг")

        self.tree.column("type", width=150)
        self.tree.column("dimensions", width=100)
        self.tree.column("material", width=120)
        self.tree.column("thickness", width=50)
        self.tree.column("qty", width=50)
        self.tree.column("area", width=80)
        self.tree.column("weight", width=80)

        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Button-3>", self._on_tree_right_click)
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="🗑️ Видалити", command=self._remove_selected).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="🧹 Очистити все", command=self._clear_all).pack(
            side=tk.LEFT, padx=2
        )
        if FREECAD_AVAILABLE:
            ttk.Button(
                btn_frame, text="🏗️ Експорт у FreeCAD", command=self._export_selected_freecad
            ).pack(side=tk.RIGHT, padx=2)

        # === ВЕРТИКАЛЬНІ ПІДСУМКИ ===
        self.summary_frame = ttk.LabelFrame(right_frame, text="📊 Підсумки", padding=5)
        self.summary_frame.pack(fill=tk.X, pady=5)

        self.summary_count_label = ttk.Label(
            self.summary_frame, text="Виробів: 0", font=("Arial", 10, "bold")
        )
        self.summary_count_label.pack(anchor="w")

        self.summary_area_label = ttk.Label(
            self.summary_frame, text="Площа: 0.000 м²", font=("Arial", 10, "bold")
        )
        self.summary_area_label.pack(anchor="w")

        self.summary_weight_label = ttk.Label(
            self.summary_frame, text="Вага: 0.000 кг", font=("Arial", 10, "bold")
        )
        self.summary_weight_label.pack(anchor="w")

    def _on_tree_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            menu = tk.Menu(self.frame, tearoff=0)
            menu.add_command(label="✏️ Змінити площу металу", command=self._edit_metal_area)
            menu.add_separator()
            menu.add_command(label="↩️ Скинути на авто-формулу", command=self._reset_metal_area)
            menu.add_separator()
            menu.add_command(label="Видалити", command=self._remove_selected)
            if FREECAD_AVAILABLE:
                menu.add_separator()
                menu.add_command(label="🏗️ Експорт .FCStd", command=self._export_selected_freecad)
                menu.add_command(label="📐 Експорт .STEP", command=self._export_selected_step)
            menu.post(event.x_root, event.y_root)

    def _on_tree_double_click(self, event):
        """Подвійний клік — редагування площі металу."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self._edit_metal_area()

    def _edit_metal_area(self):
        """Діалог зміни площі металу для вибраного виробу."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть виріб для редагування.")
            return
        idx = self.tree.index(selected[0])
        if idx < 0 or idx >= len(self.library.products):
            return
        product = self.library.products[idx]

        new_area = simpledialog.askfloat(
            "Редагування площі металу",
            f"Виріб: {product.name}\n\n"
            f"Поточна площа: {product.metal_area:.4f} м²\n"
            f"Авто-формула: {product.calculate_metal_area():.4f} м²\n\n"
            "Введіть нову площу (м²):",
            initialvalue=round(product.metal_area, 4),
            minvalue=0.0,
        )
        if new_area is None:
            return

        # Застосовуємо ручну площу та перераховуємо вагу
        product.metal_area = new_area
        product.use_custom_area = True
        product.weight = product.calculate_weight()

        self._refresh_tree()
        self._update_summary()
        if self.on_products_changed:
            self.on_products_changed()

        messagebox.showinfo(
            "Успіх",
            f"Площу металу оновлено:\n"
            f"{product.name}\n"
            f"Нова площа: {new_area:.4f} м²\n"
            f"Нова вага: {product.weight:.3f} кг",
        )

    def _reset_metal_area(self):
        """Скинути площу металу на автоматичний розрахунок."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть виріб для скидання.")
            return
        idx = self.tree.index(selected[0])
        if idx < 0 or idx >= len(self.library.products):
            return
        product = self.library.products[idx]
        product.reset_to_auto()
        self._refresh_tree()
        self._update_summary()
        if self.on_products_changed:
            self.on_products_changed()
        messagebox.showinfo(
            "Успіх",
            f"Площу скинуто на автоматичний розрахунок:\n"
            f"{product.name}\n"
            f"Нова площа: {product.metal_area:.4f} м²\n"
            f"Нова вага: {product.weight:.3f} кг",
        )

    def _export_selected_freecad(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть виріб для експорту.")
            return
        idx = self.tree.index(selected[0])
        if idx < 0 or idx >= len(self.library.products):
            return
        product = self.library.products[idx]
        filepath = filedialog.asksaveasfilename(
            defaultextension=".FCStd",
            filetypes=[("FreeCAD", "*.FCStd")],
            initialfile=f"{product.name}.FCStd",
        )
        if not filepath:
            return
        try:
            export_products_to_freecad([product], filepath, "fcstd")
            messagebox.showinfo("Успіх", f"Збережено:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Помилка", str(e))

    def _export_selected_step(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Увага", "Оберіть виріб для експорту.")
            return
        idx = self.tree.index(selected[0])
        if idx < 0 or idx >= len(self.library.products):
            return
        product = self.library.products[idx]
        filepath = filedialog.asksaveasfilename(
            defaultextension=".step",
            filetypes=[("STEP", "*.step"), ("STP", "*.stp")],
            initialfile=f"{product.name}.step",
        )
        if not filepath:
            return
        try:
            export_products_to_freecad([product], filepath, "step")
            messagebox.showinfo("Успіх", f"Збережено:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Помилка", str(e))

    def _on_type_changed(self, event=None):
        for w in self.extra_widgets:
            w.destroy()
        self.extra_widgets.clear()

        ptype = self.PRODUCT_TYPES.get(self.type_var.get(), "")
        help_text = self.HELP_TEXTS.get(ptype, "")
        self.help_label.config(text=help_text)

        if "tee" in ptype:
            # Відстань від краю до центру відгалуження
            ttk.Label(self.extra_frame, text="Відстань від краю (мм):").pack(anchor=tk.W)
            self.branch_offset_var = tk.StringVar(value="300")
            ttk.Entry(self.extra_frame, textvariable=self.branch_offset_var, width=12).pack(
                anchor=tk.W
            )

            if "rect" in ptype:
                ttk.Label(self.extra_frame, text="Відгалуження Ш×В (мм):").pack(anchor=tk.W)
                self.branch_w_var = tk.StringVar(value="200")
                self.branch_h_var = tk.StringVar(value="200")
                f = ttk.Frame(self.extra_frame)
                f.pack(fill=tk.X)
                ttk.Entry(f, textvariable=self.branch_w_var, width=8).pack(side=tk.LEFT)
                ttk.Label(f, text="×").pack(side=tk.LEFT)
                ttk.Entry(f, textvariable=self.branch_h_var, width=8).pack(side=tk.LEFT)
                self.extra_widgets.append(f)
            else:  # round_tee
                ttk.Label(self.extra_frame, text="Ø відгалуження (мм):").pack(anchor=tk.W)
                self.branch_d_var = tk.StringVar(value="200")
                ttk.Entry(self.extra_frame, textvariable=self.branch_d_var, width=12).pack(
                    anchor=tk.W
                )

            ttk.Label(self.extra_frame, text="Довжина відгалуження (мм):").pack(anchor=tk.W)
            self.branch_l_var = tk.StringVar(value="400")
            ttk.Entry(self.extra_frame, textvariable=self.branch_l_var, width=12).pack(anchor=tk.W)

        elif "transition" in ptype:
            if "rect" in ptype:
                ttk.Label(self.extra_frame, text="Кінцеві розміри Ш×В (мм):").pack(anchor=tk.W)
                self.end_w_var = tk.StringVar(value="300")
                self.end_h_var = tk.StringVar(value="150")
                f = ttk.Frame(self.extra_frame)
                f.pack(fill=tk.X)
                ttk.Entry(f, textvariable=self.end_w_var, width=8).pack(side=tk.LEFT)
                ttk.Label(f, text="×").pack(side=tk.LEFT)
                ttk.Entry(f, textvariable=self.end_h_var, width=8).pack(side=tk.LEFT)
                self.extra_widgets.append(f)
            else:  # round_transition
                ttk.Label(self.extra_frame, text="Кінцевий Ø (мм):").pack(anchor=tk.W)
                self.end_d_var = tk.StringVar(value="300")
                ttk.Entry(self.extra_frame, textvariable=self.end_d_var, width=12).pack(anchor=tk.W)

        elif "elbow" in ptype:
            ttk.Label(self.extra_frame, text="Кут згину (°):").pack(anchor=tk.W)
            self.angle_var = tk.StringVar(value="90")
            ttk.Entry(self.extra_frame, textvariable=self.angle_var, width=12).pack(anchor=tk.W)

            ttk.Label(self.extra_frame, text="Радіус дуги (мм):").pack(anchor=tk.W)
            self.radius_var = tk.StringVar(value="150")
            ttk.Entry(self.extra_frame, textvariable=self.radius_var, width=12).pack(anchor=tk.W)

        elif "cap" in ptype:
            if "rect" in ptype:
                ttk.Label(self.extra_frame, text="Ширина загину (мм):").pack(anchor=tk.W)
                self.border_var = tk.StringVar(value="25")
                ttk.Entry(self.extra_frame, textvariable=self.border_var, width=12).pack(
                    anchor=tk.W
                )
            else:  # round_cap
                ttk.Label(self.extra_frame, text="Глибина заглушки (мм):").pack(anchor=tk.W)
                self.depth_var = tk.StringVar(value="30")
                ttk.Entry(self.extra_frame, textvariable=self.depth_var, width=12).pack(anchor=tk.W)

        elif ptype == "flexible":
            ttk.Label(self.extra_frame, text="Тип тканини:").pack(anchor=tk.W)
            self.fabric_var = tk.StringVar(value="поліестер")
            ttk.Combobox(
                self.extra_frame,
                textvariable=self.fabric_var,
                values=["поліестер", "склотканина", "ПВХ"],
                state="readonly",
                width=20,
            ).pack(anchor=tk.W)

    def _add_product(self):
        try:
            ptype = self.PRODUCT_TYPES[self.type_var.get()]
            w = float(self.width_var.get())
            h = float(self.height_var.get())
            length = float(self.length_var.get())
            qty = int(self.qty_var.get())
            material = self.MATERIALS[self.material_var.get()]
            thickness = self.THICKNESSES[self.thickness_var.get()]

            product = None

            if ptype == "rect_duct":
                product = make_rect_duct(w, h, length, thickness.value, material, qty)
            elif ptype == "round_duct":
                product = make_round_duct(h, length, thickness.value, material, qty)
            elif ptype == "rect_flange":
                product = RectFlange(
                    name=f"Фланець {w:.0f}×{h:.0f}",
                    width=w,
                    height=h,
                    length=0,
                    thickness=thickness,
                    material=material,
                    quantity=qty,
                    flange_border=30,
                )
            elif ptype == "round_flange":
                product = RoundFlange(
                    name=f"Фланець Ø{h:.0f}",
                    width=h,
                    height=h,
                    length=0,
                    thickness=thickness,
                    material=material,
                    quantity=qty,
                    flange_width=30,
                )
            elif ptype == "rect_tee":
                bw = float(getattr(self, "branch_w_var", tk.StringVar(value="200")).get())
                bh = float(getattr(self, "branch_h_var", tk.StringVar(value="200")).get())
                bl = float(getattr(self, "branch_l_var", tk.StringVar(value="400")).get())
                offset = float(getattr(self, "branch_offset_var", tk.StringVar(value="300")).get())
                product = RectTee(
                    name=f"Трійник {w:.0f}×{h:.0f}/{bw:.0f}×{bh:.0f}",
                    width=w,
                    height=h,
                    length=length,
                    thickness=thickness,
                    material=material,
                    quantity=qty,
                    branch_width=bw,
                    branch_height=bh,
                    branch_length=bl,
                    branch_offset=offset,
                )
            elif ptype == "round_tee":
                bd = float(getattr(self, "branch_d_var", tk.StringVar(value="200")).get())
                bl = float(getattr(self, "branch_l_var", tk.StringVar(value="400")).get())
                offset = float(getattr(self, "branch_offset_var", tk.StringVar(value="300")).get())
                product = RoundTee(
                    name=f"Трійник Ø{h:.0f}/Ø{bd:.0f}",
                    width=h,
                    height=h,
                    length=length,
                    thickness=thickness,
                    material=material,
                    quantity=qty,
                    branch_diameter=bd,
                    branch_length=bl,
                    branch_offset=offset,
                )
            elif ptype == "rect_transition":
                ew = float(getattr(self, "end_w_var", tk.StringVar(value="300")).get())
                eh = float(getattr(self, "end_h_var", tk.StringVar(value="150")).get())
                product = RectTransition(
                    name=f"Перехід {w:.0f}×{h:.0f}→{ew:.0f}×{eh:.0f}",
                    width=w,
                    height=h,
                    length=length,
                    thickness=thickness,
                    material=material,
                    quantity=qty,
                    end_width=ew,
                    end_height=eh,
                )
            elif ptype == "round_transition":
                ed = float(getattr(self, "end_d_var", tk.StringVar(value="300")).get())
                product = RoundTransition(
                    name=f"Перехід Ø{h:.0f}→Ø{ed:.0f}",
                    width=h,
                    height=h,
                    length=length,
                    thickness=thickness,
                    material=material,
                    quantity=qty,
                    end_diameter=ed,
                )
            elif ptype == "rect_elbow":
                angle = float(getattr(self, "angle_var", tk.StringVar(value="90")).get())
                radius = float(getattr(self, "radius_var", tk.StringVar(value="150")).get())
                product = RectElbow(
                    name=f"Відвід {w:.0f}×{h:.0f} {angle:.0f}°",
                    width=w,
                    height=h,
                    length=length,
                    thickness=thickness,
                    material=material,
                    quantity=qty,
                    angle=angle,
                    radius=radius,
                )
            elif ptype == "round_elbow":
                angle = float(getattr(self, "angle_var", tk.StringVar(value="90")).get())
                radius = float(getattr(self, "radius_var", tk.StringVar(value="150")).get())
                product = RoundElbow(
                    name=f"Відвід Ø{h:.0f} {angle:.0f}°",
                    width=h,
                    height=h,
                    length=length,
                    thickness=thickness,
                    material=material,
                    quantity=qty,
                    angle=angle,
                    radius=radius,
                )
            elif ptype == "rect_cap":
                border = float(getattr(self, "border_var", tk.StringVar(value="25")).get())
                product = RectCap(
                    name=f"Заглушка {w:.0f}×{h:.0f}",
                    width=w,
                    height=h,
                    length=0,
                    thickness=thickness,
                    material=material,
                    quantity=qty,
                    flange_border=border,
                )
            elif ptype == "round_cap":
                depth = float(getattr(self, "depth_var", tk.StringVar(value="30")).get())
                product = RoundCap(
                    name=f"Заглушка Ø{h:.0f}",
                    width=h,
                    height=h,
                    length=0,
                    thickness=thickness,
                    material=material,
                    quantity=qty,
                    depth=depth,
                )
            elif ptype == "flexible":
                fabric = getattr(self, "fabric_var", tk.StringVar(value="поліестер")).get()
                product = FlexibleConnector(
                    name=f"Гнучка вставка {w:.0f}×{h:.0f}",
                    width=w,
                    height=h,
                    length=length,
                    thickness=thickness,
                    material=material,
                    quantity=qty,
                    fabric_type=fabric,
                )

            if product:
                self.library.add(product)
                self._refresh_tree()
                self._update_summary()
                if self.on_products_changed:
                    self.on_products_changed()
            else:
                messagebox.showerror("Помилка", f"Тип виробу '{ptype}' ще не реалізовано.")

        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося додати виріб:\n{str(e)}")

    def _refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for p in self.library.products:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    p.product_type,
                    f"{p.width:.0f}×{p.height:.0f}×{p.length:.0f}",
                    p.material.value,
                    p.thickness.value,
                    p.quantity,
                    f"{p.metal_area:.3f}",
                    f"{p.weight:.3f}",
                ),
            )

    def _update_summary(self):
        total = len(self.library)
        area = self.library.get_total_metal_area()
        weight = self.library.get_total_weight()
        self.summary_count_label.config(text=f"Виробів: {total}")
        self.summary_area_label.config(text=f"Площа: {area:.3f} м²")
        self.summary_weight_label.config(text=f"Вага: {weight:.3f} кг")

    def _remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = self.tree.index(selected[0])
        if 0 <= idx < len(self.library.products):
            del self.library.products[idx]
            self._refresh_tree()
            self._update_summary()
            if self.on_products_changed:
                self.on_products_changed()

    def _clear_all(self):
        if messagebox.askyesno("Підтвердження", "Видалити всі вироби?"):
            self.library.clear()
            self._refresh_tree()
            self._update_summary()
            if self.on_products_changed:
                self.on_products_changed()

    def get_library(self):
        return self.library

    def get_products_dict(self):
        return self.library.to_dict()
