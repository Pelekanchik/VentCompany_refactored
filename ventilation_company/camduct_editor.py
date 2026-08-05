#!/usr/bin/env python3
"""
Графічний редактор розкрою листового металу (CamDuct-подібний)
Модуль: вкладка "Розкрій листа"
"""
import json
import math
import random
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk


class SheetPart:
    """Одна деталь для розкрою"""

    def __init__(self, part_type, name, width, height, quantity=1, color=None, rotated=False):
        self.part_type = part_type  # 'rect_duct', 'round_duct', 'elbow', 'tee', 'transition'
        self.name = name
        self.width = width  # мм (для розгортки)
        self.height = height  # мм (довжина розгортки)
        self.quantity = quantity
        self.color = color or self._random_color()
        self.area = width * height / 1_000_000  # м²
        self.placed = False
        self.sheet_index = -1
        self.x = 0
        self.y = 0
        self.rotated = rotated

    def _random_color(self):
        colors = [
            "#e74c3c",
            "#3498db",
            "#2ecc71",
            "#f39c12",
            "#9b59b6",
            "#1abc9c",
            "#e67e22",
            "#34495e",
            "#16a085",
            "#d35400",
            "#2980b9",
            "#8e44ad",
            "#27ae60",
            "#c0392b",
            "#f1c40f",
        ]
        return random.choice(colors)

    def __repr__(self):
        return f"{self.name} ({self.width}x{self.height} мм, {self.quantity} шт)"


class NestingEngine:
    """Двовимірний алгоритм розкладки (Bottom-Left heuristic)"""

    def __init__(self, sheet_width, sheet_height, blade_kerf=3):
        self.sheet_w = sheet_width  # мм
        self.sheet_h = sheet_height  # мм
        self.kerf = blade_kerf  # мм (ширина пропилу)
        self.sheets = []  # список листів, кожен — список розміщених деталей

    def reset(self):
        self.sheets = []

    def nest(self, parts):
        """Розкладка всіх деталей. Повертає кількість листів."""
        self.reset()
        # Розгортаємо кількість: кожна деталь окремо
        flat_parts = []
        for p in parts:
            for _ in range(p.quantity):
                flat_parts.append(SheetPart(p.part_type, p.name, p.width, p.height, 1, p.color))
        # Сортуємо за площею (спочатку більші)
        flat_parts.sort(key=lambda x: x.width * x.height, reverse=True)

        for part in flat_parts:
            placed = False
            for idx, sheet in enumerate(self.sheets):
                pos = self._find_position(sheet, part)
                if pos:
                    part.x, part.y = pos
                    part.sheet_index = idx
                    sheet.append(part)
                    placed = True
                    break
            if not placed:
                # Новий лист
                part.x, part.y = (0, 0)
                part.sheet_index = len(self.sheets)
                self.sheets.append([part])
        return len(self.sheets)

    def _find_position(self, sheet, part):
        """Bottom-left heuristic з ротацією 90°: шукаємо найнижчу, потім найлівішу позицію"""
        candidates = [(0, 0)]
        # Додаємо кандидатів — кути праворуч і зверху від кожної розміщеної деталі
        for placed in sheet:
            candidates.append((placed.x + placed.width + self.kerf, placed.y))
            candidates.append((placed.x, placed.y + placed.height + self.kerf))
        # Перевіряємо кожен кандидат з обома орієнтаціями
        best = None
        best_rotated = False
        orientations = [(part.width, part.height, False)]
        if part.width != part.height:
            orientations.append((part.height, part.width, True))

        for pw, ph, is_rotated in orientations:
            for cx, cy in candidates:
                if (
                    cx + pw <= self.sheet_w
                    and cy + ph <= self.sheet_h
                    and self._no_overlap(sheet, pw, ph, cx, cy)
                    and (best is None or cy < best[1] or (cy == best[1] and cx < best[0]))
                ):
                    best = (cx, cy)
                    best_rotated = is_rotated

        if best and best_rotated:
            part.width, part.height = part.height, part.width
            part.rotated = True
        return best

    def _no_overlap(self, sheet, pw, ph, cx, cy):
        for p in sheet:
            if not (
                cx + pw + self.kerf <= p.x
                or cx >= p.x + p.width + self.kerf
                or cy + ph + self.kerf <= p.y
                or cy >= p.y + p.height + self.kerf
            ):
                return False
        return True

    def get_stats(self):
        total_area = sum(p.width * p.height for sheet in self.sheets for p in sheet)
        sheet_area = self.sheet_w * self.sheet_h * len(self.sheets)
        utilization = (total_area / sheet_area * 100) if sheet_area > 0 else 0
        return {
            "sheets_count": len(self.sheets),
            "sheet_area_m2": self.sheet_w * self.sheet_h / 1_000_000,
            "total_parts_area_m2": total_area / 1_000_000,
            "utilization_percent": round(utilization, 2),
            "waste_percent": round(100 - utilization, 2),
        }


class CamDuctEditorFrame(tk.Frame):
    """Головний фрейм редактора розкрою"""

    STANDARD_SHEETS = {
        "1250 x 2500 мм": (1250, 2500),
        "1500 x 3000 мм": (1500, 3000),
        "1000 x 2000 мм": (1000, 2000),
        "1250 x 3000 мм": (1250, 3000),
    }

    def __init__(self, parent, colors=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.colors = colors or {
            "bg": "#f0f0f0",
            "fg": "#333333",
            "accent": "#3498db",
            "card": "white",
            "sidebar": "#2c3e50",
            "sidebar_fg": "white",
        }
        self.configure(bg=self.colors["bg"])

        self.parts = []  # список SheetPart
        self.nesting = None  # NestingEngine
        self.scale = 0.15  # px на мм
        self.current_sheet = 0  # поточний лист для перегляду

        print("[CamDuct] __init__ start")
        print("[CamDuct] build_ui start")
        self.build_ui()
        print("[CamDuct] build_ui done")
        print("[CamDuct] __init__ done")

    # ═══════════════════════════════════════════════════════
    #  ІНТЕРФЕЙС
    # ═══════════════════════════════════════════════════════
    def build_ui(self):
        # === ЛІВА ПАНЕЛЬ: інструменти та деталі з прокруткою ===
        left = tk.Frame(self, bg=self.colors["card"], width=360, bd=1, relief=tk.RIDGE)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left.pack_propagate(False)

        left_canvas = tk.Canvas(left, bg=self.colors["card"], highlightthickness=0, width=340)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        left_vsb = ttk.Scrollbar(left, orient="vertical", command=left_canvas.yview)
        left_vsb.pack(side=tk.RIGHT, fill="y")
        left_canvas.configure(yscrollcommand=left_vsb.set)

        # Внутрішній фрейм для всіх елементів
        inner = tk.Frame(left_canvas, bg=self.colors["card"], width=340)
        left_canvas.create_window((0, 0), window=inner, anchor="nw", width=340)

        def _on_inner_configure(event=None):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))

        inner.bind("<Configure>", _on_inner_configure)

        # Прокрутка колесом миші
        def _on_mousewheel(event):
            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        left_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # --- Параметри листа ---
        sheet_frame = tk.LabelFrame(
            inner,
            text="📐 Параметри листа",
            bg=self.colors["card"],
            fg=self.colors["fg"],
            font=("Segoe UI", 11, "bold"),
            padx=8,
            pady=8,
        )
        sheet_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        tk.Label(
            sheet_frame, text="Стандартний розмір:", bg=self.colors["card"], font=("Segoe UI", 10)
        ).pack(anchor=tk.W)
        self.sheet_combo = ttk.Combobox(
            sheet_frame,
            values=list(self.STANDARD_SHEETS.keys()),
            state="readonly",
            font=("Segoe UI", 10),
            width=28,
        )
        self.sheet_combo.current(0)
        self.sheet_combo.pack(fill=tk.X, pady=(2, 6))
        self.sheet_combo.bind("<<ComboboxSelected>>", lambda e: self.draw_nesting())

        dim_frame = tk.Frame(sheet_frame, bg=self.colors["card"])
        dim_frame.pack(fill=tk.X)
        tk.Label(dim_frame, text="Ширина:", bg=self.colors["card"], font=("Segoe UI", 10)).pack(
            side=tk.LEFT
        )
        self.sheet_w_entry = tk.Entry(dim_frame, width=8, font=("Segoe UI", 10))
        self.sheet_w_entry.insert(0, "1250")
        self.sheet_w_entry.pack(side=tk.LEFT, padx=(4, 12))
        tk.Label(dim_frame, text="Висота:", bg=self.colors["card"], font=("Segoe UI", 10)).pack(
            side=tk.LEFT
        )
        self.sheet_h_entry = tk.Entry(dim_frame, width=8, font=("Segoe UI", 10))
        self.sheet_h_entry.insert(0, "2500")
        self.sheet_h_entry.pack(side=tk.LEFT, padx=4)
        tk.Label(dim_frame, text="мм", bg=self.colors["card"], font=("Segoe UI", 10)).pack(
            side=tk.LEFT
        )

        tk.Label(
            sheet_frame, text="Пропил (керф):", bg=self.colors["card"], font=("Segoe UI", 10)
        ).pack(anchor=tk.W, pady=(6, 2))
        self.kerf_entry = tk.Entry(sheet_frame, width=8, font=("Segoe UI", 10))
        self.kerf_entry.insert(0, "3")
        self.kerf_entry.pack(anchor=tk.W)

        # --- Додавання деталі ---
        add_frame = tk.LabelFrame(
            inner,
            text="➕ Додати деталь",
            bg=self.colors["card"],
            fg=self.colors["fg"],
            font=("Segoe UI", 11, "bold"),
            padx=8,
            pady=8,
        )
        add_frame.pack(fill=tk.X, padx=8, pady=4)

        tk.Label(add_frame, text="Тип виробу:", bg=self.colors["card"], font=("Segoe UI", 10)).pack(
            anchor=tk.W
        )
        self.part_type = ttk.Combobox(
            add_frame,
            values=[
                "Прямокутний повітропровід",
                "Круглий повітропровід",
                "Відведення (коліно)",
                "Трійник",
                "Перехід",
                "Заглушка",
                "Прямокутне відведення",
                "Прямокутний трійник",
                "Прямокутний перехід",
                "Решітка",
                "Заслінка",
            ],
            state="readonly",
            font=("Segoe UI", 10),
            width=28,
        )
        self.part_type.current(0)
        self.part_type.pack(fill=tk.X, pady=(2, 6))
        self.part_type.bind("<<ComboboxSelected>>", self.on_part_type_change)

        # Динамічні поля розмірів
        self.size_container = tk.Frame(add_frame, bg=self.colors["card"])
        self.size_container.pack(fill=tk.X, pady=2)
        self.size_entries = {}
        self.build_size_inputs("rect_duct")

        tk.Label(add_frame, text="Кількість:", bg=self.colors["card"], font=("Segoe UI", 10)).pack(
            anchor=tk.W, pady=(4, 2)
        )
        self.part_qty = tk.Entry(add_frame, width=8, font=("Segoe UI", 10))
        self.part_qty.insert(0, "1")
        self.part_qty.pack(anchor=tk.W)

        btn_frame = tk.Frame(add_frame, bg=self.colors["card"])
        btn_frame.pack(fill=tk.X, pady=8)
        tk.Button(
            btn_frame,
            text="➕ Додати",
            bg=self.colors["accent"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            command=self.add_part,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(
            btn_frame,
            text="🗑 Очистити",
            bg="#e74c3c",
            fg="white",
            font=("Segoe UI", 10),
            command=self.clear_parts,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        # --- Список деталей ---
        list_frame = tk.LabelFrame(
            inner,
            text="📋 Список деталей",
            bg=self.colors["card"],
            fg=self.colors["fg"],
            font=("Segoe UI", 11, "bold"),
            padx=8,
            pady=4,
        )
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        cols = ("№", "Назва", "Розмір", "К-ть", "Площа")
        # Стандартний стиль — без кастомного DC.Treeview (може конфліктувати)
        self.parts_tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=6)
        for c in cols:
            self.parts_tree.heading(c, text=c)
        self.parts_tree.column("№", width=35, anchor="center", stretch=False)
        self.parts_tree.column("Назва", width=110, anchor="w")
        self.parts_tree.column("Розмір", width=95, anchor="center")
        self.parts_tree.column("К-ть", width=45, anchor="center")
        self.parts_tree.column("Площа", width=65, anchor="center")
        self.parts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.parts_tree.yview)
        self.parts_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill="y")

        btn2 = tk.Frame(inner, bg=self.colors["card"])
        btn2.pack(fill=tk.X, padx=8, pady=4)
        tk.Button(
            btn2,
            text="❌ Видалити вибрану",
            bg="#c0392b",
            fg="white",
            font=("Segoe UI", 10),
            command=self.delete_selected_part,
        ).pack(fill=tk.X)

        # --- Кнопки дії ---
        act_frame = tk.Frame(inner, bg=self.colors["card"])
        act_frame.pack(fill=tk.X, padx=8, pady=(4, 8))
        tk.Button(
            act_frame,
            text="🧮 РОЗКРИТИ",
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            command=self.run_nesting,
        ).pack(fill=tk.X, pady=2)
        tk.Button(
            act_frame,
            text="💾 Зберегти розкрій",
            bg="#2980b9",
            fg="white",
            font=("Segoe UI", 11),
            command=self.save_nesting,
        ).pack(fill=tk.X, pady=2)
        tk.Button(
            act_frame,
            text="📊 Експорт CSV",
            bg="#8e44ad",
            fg="white",
            font=("Segoe UI", 11),
            command=self.export_csv,
        ).pack(fill=tk.X, pady=2)

        # === ЦЕНТР: Canvas ===
        center = tk.Frame(self, bg=self.colors["bg"])
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Toolbar над canvas
        toolbar = tk.Frame(center, bg=self.colors["sidebar"], height=36)
        toolbar.pack(fill=tk.X, pady=(0, 4))
        toolbar.pack_propagate(False)

        tk.Label(
            toolbar,
            text="🔍 Масштаб:",
            bg=self.colors["sidebar"],
            fg="white",
            font=("Segoe UI", 10),
        ).pack(side=tk.LEFT, padx=10)
        self.scale_var = tk.DoubleVar(value=0.15)
        ttk.Scale(
            toolbar,
            from_=0.05,
            to=0.5,
            variable=self.scale_var,
            orient=tk.HORIZONTAL,
            length=150,
            command=lambda e: self.draw_nesting(),
        ).pack(side=tk.LEFT, padx=5)
        self.scale_label = tk.Label(
            toolbar,
            text="0.15 px/мм",
            bg=self.colors["sidebar"],
            fg="white",
            font=("Segoe UI", 10),
            width=12,
        )
        self.scale_label.pack(side=tk.LEFT)

        tk.Label(
            toolbar, text="📄 Лист:", bg=self.colors["sidebar"], fg="white", font=("Segoe UI", 10)
        ).pack(side=tk.LEFT, padx=(20, 5))
        self.sheet_nav_var = tk.StringVar(value="Лист 1")
        self.sheet_nav = ttk.Combobox(
            toolbar,
            textvariable=self.sheet_nav_var,
            values=["Лист 1"],
            state="readonly",
            font=("Segoe UI", 10),
            width=12,
        )
        self.sheet_nav.pack(side=tk.LEFT)
        self.sheet_nav.bind("<<ComboboxSelected>>", self.on_sheet_nav)

        tk.Button(
            toolbar,
            text="◀",
            bg=self.colors["sidebar"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            command=self.prev_sheet,
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            toolbar,
            text="▶",
            bg=self.colors["sidebar"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            command=self.next_sheet,
        ).pack(side=tk.LEFT, padx=2)

        # Canvas з прокруткою (pack-версія)
        canvas_frame = tk.Frame(center, bg=self.colors["bg"], bd=1, relief=tk.SUNKEN)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            canvas_frame, bg="#e8e8e8", width=600, height=400, highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        vsb.pack(side=tk.RIGHT, fill="y")
        hsb = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        hsb.pack(side=tk.BOTTOM, fill="x")
        self.canvas.configure(xscrollcommand=hsb.set, yscrollcommand=vsb.set)

        # Тестовий фон
        self._draw_placeholder()

        # === ПРАВА ПАНЕЛЬ: результати ===
        right = tk.Frame(self, bg=self.colors["card"], width=240, bd=1, relief=tk.RIDGE)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        right.pack_propagate(False)

        res_frame = tk.LabelFrame(
            right,
            text="📊 Результат розкрою",
            bg=self.colors["card"],
            fg=self.colors["fg"],
            font=("Segoe UI", 11, "bold"),
            padx=10,
            pady=10,
        )
        res_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        self.res_sheets = tk.Label(
            res_frame,
            text="—",
            font=("Segoe UI", 18, "bold"),
            bg=self.colors["card"],
            fg=self.colors["accent"],
        )
        self.res_sheets.pack()
        tk.Label(
            res_frame,
            text="Листів металу",
            bg=self.colors["card"],
            fg="#666",
            font=("Segoe UI", 10),
        ).pack()

        ttk.Separator(res_frame, orient="horizontal").pack(fill=tk.X, pady=10)

        self.res_util = tk.Label(
            res_frame, text="—", font=("Segoe UI", 16, "bold"), bg=self.colors["card"], fg="#27ae60"
        )
        self.res_util.pack()
        tk.Label(
            res_frame,
            text="Використання листа",
            bg=self.colors["card"],
            fg="#666",
            font=("Segoe UI", 10),
        ).pack()

        ttk.Separator(res_frame, orient="horizontal").pack(fill=tk.X, pady=10)

        self.res_area = tk.Label(
            res_frame, text="—", font=("Segoe UI", 14, "bold"), bg=self.colors["card"]
        )
        self.res_area.pack()
        tk.Label(
            res_frame,
            text="Площа деталей",
            bg=self.colors["card"],
            fg="#666",
            font=("Segoe UI", 10),
        ).pack()

        self.res_waste = tk.Label(
            res_frame, text="—", font=("Segoe UI", 14, "bold"), bg=self.colors["card"], fg="#c0392b"
        )
        self.res_waste.pack(pady=(10, 0))
        tk.Label(
            res_frame, text="Відходи", bg=self.colors["card"], fg="#666", font=("Segoe UI", 10)
        ).pack()

        # Детальна статистика
        detail_frame = tk.LabelFrame(
            right,
            text="📈 Деталі",
            bg=self.colors["card"],
            fg=self.colors["fg"],
            font=("Segoe UI", 11, "bold"),
            padx=8,
            pady=8,
        )
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.detail_text = tk.Text(
            detail_frame,
            wrap="word",
            font=("Segoe UI", 10),
            bg="#fafafa",
            relief=tk.FLAT,
            height=12,
            state="disabled",
        )
        self.detail_text.pack(fill=tk.BOTH, expand=True)

        # Підказка
        hint = tk.Label(
            right,
            text="💡 Порада: додайте деталі, натисніть «РОЗКРИТИ»\n"
            "і переглядайте кожен лист стрілками ◀ ▶",
            bg=self.colors["card"],
            fg="#666",
            font=("Segoe UI", 9),
            wraplength=240,
            justify="center",
        )
        hint.pack(fill=tk.X, padx=8, pady=8)

    # ═══════════════════════════════════════════════════════
    #  ЛОГІКА ДЕТАЛЕЙ
    # ═══════════════════════════════════════════════════════
    def build_size_inputs(self, part_type):
        """Створює поля вводу розмірів залежно від типу деталі"""
        print(f"[CamDuct] build_size_inputs for: {part_type}")
        for w in self.size_container.winfo_children():
            w.destroy()
        self.size_entries = {}

        configs = {
            "rect_duct": [
                ("width", "Ширина", "400"),
                ("height", "Висота", "250"),
                ("length", "Довжина", "1000"),
            ],
            "round_duct": [("diameter", "Діаметр", "250"), ("length", "Довжина", "1000")],
            "elbow": [("diameter", "Діаметр", "250"), ("angle", "Кут", "90")],
            "tee": [("diameter", "Діаметр", "250")],
            "transition": [
                ("d1", "Вхідний діам.", "250"),
                ("d2", "Вихідний діам.", "200"),
                ("length", "Довжина", "300"),
            ],
            "cap": [("diameter", "Діаметр", "250")],
            "rect_elbow": [
                ("width", "Ширина", "400"),
                ("height", "Висота", "250"),
                ("angle", "Кут", "90"),
            ],
            "rect_tee": [("width", "Ширина", "400"), ("height", "Висота", "250")],
            "rect_transition": [
                ("w1", "Вхід. шир.", "400"),
                ("h1", "Вхід. вис.", "250"),
                ("w2", "Вихід. шир.", "300"),
                ("h2", "Вихід. вис.", "200"),
                ("length", "Довжина", "300"),
            ],
            "grille": [("width", "Ширина", "300"), ("height", "Висота", "150")],
            "damper": [("diameter", "Діаметр", "250")],
        }

        mapping = {
            "Прямокутний повітропровід": "rect_duct",
            "Круглий повітропровід": "round_duct",
            "Відведення (коліно)": "elbow",
            "Трійник": "tee",
            "Перехід": "transition",
            "Заглушка": "cap",
            "Прямокутне відведення": "rect_elbow",
            "Прямокутний трійник": "rect_tee",
            "Прямокутний перехід": "rect_transition",
            "Решітка": "grille",
            "Заслінка": "damper",
        }
        ptype = mapping.get(part_type, "rect_duct")
        fields = configs.get(ptype, [])

        for _i, (key, label, default) in enumerate(fields):
            row = tk.Frame(self.size_container, bg=self.colors["card"])
            row.pack(fill=tk.X, pady=2)
            tk.Label(
                row,
                text=f"{label}:",
                bg=self.colors["card"],
                font=("Segoe UI", 10),
                width=12,
                anchor="e",
            ).pack(side=tk.LEFT, padx=(0, 4))
            e = tk.Entry(row, width=10, font=("Segoe UI", 10))
            e.insert(0, default)
            e.pack(side=tk.LEFT)
            tk.Label(row, text="мм", bg=self.colors["card"], font=("Segoe UI", 9)).pack(
                side=tk.LEFT, padx=(4, 0)
            )
            self.size_entries[key] = e

    def on_part_type_change(self, event=None):
        self.build_size_inputs(self.part_type.get())

    def calculate_unfold(self, part_type, sizes):
        """Розраховує розміри розгортки (width x height в мм)"""
        mapping = {
            "Прямокутний повітропровід": "rect_duct",
            "Круглий повітропровід": "round_duct",
            "Відведення (коліно)": "elbow",
            "Трійник": "tee",
            "Перехід": "transition",
            "Заглушка": "cap",
            "Прямокутне відведення": "rect_elbow",
            "Прямокутний трійник": "rect_tee",
            "Прямокутний перехід": "rect_transition",
            "Решітка": "grille",
            "Заслінка": "damper",
        }
        pt = mapping.get(part_type, "rect_duct")

        if pt == "rect_duct":
            w = float(sizes.get("width", 400))
            h = float(sizes.get("height", 250))
            length = float(sizes.get("length", 1000))
            unfold_w = 2 * (w + h) + 6  # периметр + 6 мм на фальці
            unfold_h = length
            name = f"Прямокутник {int(w)}x{int(h)}x{int(length)}"

        elif pt == "round_duct":
            d = float(sizes.get("diameter", 250))
            length = float(sizes.get("length", 1000))
            unfold_w = math.pi * (d + 6)  # π*(d+6) — з урахуванням фальця
            unfold_h = length
            name = f"Круглий Ø{int(d)}x{int(length)}"

        elif pt == "elbow":
            d = float(sizes.get("diameter", 250))
            angle = float(sizes.get("angle", 90))
            # Розгортка відведення: π*(d+6) * d * (angle/90) * 1.35
            unfold_w = math.pi * (d + 6)
            unfold_h = d * (angle / 90) * 1.35
            name = f"Відведення Ø{int(d)}°{int(angle)}"

        elif pt == "tee":
            d = float(sizes.get("diameter", 250))
            unfold_w = math.pi * (d + 6)
            unfold_h = d * 1.55
            name = f"Трійник Ø{int(d)}"

        elif pt == "transition":
            d1 = float(sizes.get("d1", 250))
            d2 = float(sizes.get("d2", 200))
            length = float(sizes.get("length", 300))
            unfold_w = math.pi * ((d1 + d2) / 2 + 6)
            unfold_h = length * 1.25
            name = f"Перехід Ø{int(d1)}→Ø{int(d2)}"

        elif pt == "cap":
            d = float(sizes.get("diameter", 250))
            unfold_w = math.pi * (d + 6)
            unfold_h = d * 0.8
            name = f"Заглушка Ø{int(d)}"

        elif pt == "rect_elbow":
            w = float(sizes.get("width", 400))
            h = float(sizes.get("height", 250))
            angle = float(sizes.get("angle", 90))
            unfold_w = 2 * (w + h) + 6
            unfold_h = ((w + h) / 2) * (angle / 90) * 1.35
            name = f"Прям. відведення {int(w)}x{int(h)}°{int(angle)}"

        elif pt == "rect_tee":
            w = float(sizes.get("width", 400))
            h = float(sizes.get("height", 250))
            unfold_w = 2 * (w + h) + 6
            unfold_h = ((w + h) / 2) * 1.65
            name = f"Прям. трійник {int(w)}x{int(h)}"

        elif pt == "rect_transition":
            w1 = float(sizes.get("w1", 400))
            h1 = float(sizes.get("h1", 250))
            w2 = float(sizes.get("w2", 300))
            h2 = float(sizes.get("h2", 200))
            length = float(sizes.get("length", 300))
            unfold_w = 2 * ((w1 + h1 + w2 + h2) / 2 + 6)
            unfold_h = length * 1.3
            name = f"Прям. перехід {int(w1)}x{int(h1)}→{int(w2)}x{int(h2)}"

        elif pt == "grille":
            w = float(sizes.get("width", 300))
            h = float(sizes.get("height", 150))
            unfold_w = w * 2.5
            unfold_h = h * 2.5
            name = f"Решітка {int(w)}x{int(h)}"

        elif pt == "damper":
            d = float(sizes.get("diameter", 250))
            unfold_w = math.pi * (d + 6)
            unfold_h = d * 1.8
            name = f"Заслінка Ø{int(d)}"

        else:
            unfold_w = 100
            unfold_h = 100
            name = "Невідома деталь"

        return round(unfold_w, 1), round(unfold_h, 1), name

    def add_part(self):
        print(f"[CamDuct] add_part clicked. size_entries keys: {list(self.size_entries.keys())}")
        part_type = self.part_type.get()
        print(f"[CamDuct] part_type: {part_type}")

        sizes = {}
        for k, v in self.size_entries.items():
            val = v.get()
            print(f"[CamDuct]   {k} = '{val}'")
            sizes[k] = float(val or 0)

        qty_str = self.part_qty.get()
        print(f"[CamDuct] qty: '{qty_str}'")
        qty = int(qty_str or 1)

        try:
            uw, uh, name = self.calculate_unfold(part_type, sizes)
            print(f"[CamDuct] unfold: {uw}x{uh}, name: {name}")
        except Exception as e:
            print(f"[CamDuct] ERROR in calculate_unfold: {e}")
            messagebox.showwarning("Помилка", f"Некоректні розміри: {e}")
            return

        part = SheetPart(part_type, name, uw, uh, qty)
        self.parts.append(part)
        print(f"[CamDuct] part added. Total parts: {len(self.parts)}")
        self.refresh_parts_tree()

    def delete_selected_part(self):
        sel = self.parts_tree.selection()
        if not sel:
            return
        idx = self.parts_tree.index(sel[0])
        del self.parts[idx]
        self.refresh_parts_tree()

    def clear_parts(self):
        self.parts.clear()
        self.refresh_parts_tree()
        self.canvas.delete("all")
        self.reset_results()

    def import_calc_items(self, calc_items, clear_existing=True):
        """Імпортує деталі з DetailCalculatorFrame у список розкрою"""
        mapping = {
            "Круглі повітропроводи": "Круглий повітропровід",
            "Прямокутні повітропроводи": "Прямокутний повітропровід",
            "Відведення (коліно)": "Відведення (коліно)",
            "Трійник": "Трійник",
            "Перехід": "Перехід",
            "Заглушка": "Заглушка",
            "Прямокутне відведення": "Прямокутне відведення",
            "Прямокутний трійник": "Прямокутний трійник",
            "Прямокутний перехід": "Прямокутний перехід",
            "Решітка вентиляційна": "Решітка",
            "Заслінка повітряна": "Заслінка",
        }
        if clear_existing:
            self.parts.clear()
        added = 0
        for item in calc_items:
            subtype_name = item.get("subtype_name", "")
            part_type = mapping.get(subtype_name)
            if not part_type:
                print(f"[CamDuct] Пропущено (невідомий тип): {subtype_name}")
                continue
            params = item.get("params", {})
            qty = item.get("quantity", 1)
            try:
                uw, uh, name = self.calculate_unfold(part_type, params)
                part = SheetPart(part_type, name, uw, uh, qty)
                self.parts.append(part)
                added += 1
                print(f"[CamDuct] Імпортовано: {name} x{qty} ({uw:.0f}x{uh:.0f})")
            except Exception as e:
                print(f"[CamDuct] Помилка імпорту {subtype_name}: {e}")
        self.refresh_parts_tree()
        return added

    def refresh_parts_tree(self):
        print(f"[CamDuct] refresh_parts_tree called, parts count: {len(self.parts)}")
        for row in self.parts_tree.get_children():
            self.parts_tree.delete(row)
        total_area = 0
        for i, p in enumerate(self.parts, 1):
            area = p.area * p.quantity
            total_area += area
            self.parts_tree.insert(
                "",
                "end",
                values=(i, p.name, f"{p.width:.0f}x{p.height:.0f}", p.quantity, f"{area:.3f}"),
            )
            print(f"[CamDuct]   inserted row {i}: {p.name}")
        # Підсумок у статусі
        self.res_area.config(text=f"{total_area:.3f} м²")
        print("[CamDuct] refresh done")

    # ═══════════════════════════════════════════════════════
    #  РОЗКРІЙ (NESTING)
    # ═══════════════════════════════════════════════════════
    def run_nesting(self):
        print(f"[CamDuct] run_nesting clicked. parts: {len(self.parts)}")
        if not self.parts:
            messagebox.showwarning("Увага", "Додайте хоча б одну деталь!")
            return

        try:
            sw = int(self.sheet_w_entry.get())
            sh = int(self.sheet_h_entry.get())
            kerf = int(self.kerf_entry.get())
            print(f"[CamDuct] sheet: {sw}x{sh}, kerf: {kerf}")
        except ValueError as e:
            print(f"[CamDuct] ERROR parsing sheet: {e}")
            messagebox.showwarning("Помилка", "Введіть коректні розміри листа")
            return

        self.nesting = NestingEngine(sw, sh, kerf)
        sheets_needed = self.nesting.nest(self.parts)
        stats = self.nesting.get_stats()
        print(
            f"[CamDuct] nesting done. sheets: {sheets_needed}, util: {stats['utilization_percent']}%"
        )

        self.res_sheets.config(text=str(sheets_needed))
        self.res_util.config(text=f"{stats['utilization_percent']}%")
        self.res_area.config(text=f"{stats['total_parts_area_m2']:.3f} м²")
        self.res_waste.config(text=f"{stats['waste_percent']}%")

        # Оновлюємо навігацію по листах
        self.sheet_nav["values"] = [f"Лист {i+1}" for i in range(sheets_needed)]
        self.current_sheet = 0
        if sheets_needed > 0:
            self.sheet_nav.current(0)

        # Детальний текст
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert(
            "1.0",
            f"Розмір листа: {sw} x {sh} мм\n"
            f"Площа одного листа: {stats['sheet_area_m2']:.3f} м²\n"
            f"Всього листів: {stats['sheets_count']}\n"
            f"Загальна площа листів: {stats['sheets_count'] * stats['sheet_area_m2']:.3f} м²\n"
            f"Площа деталей: {stats['total_parts_area_m2']:.3f} м²\n"
            f"Коеф. використання: {stats['utilization_percent']}%\n"
            f"Відходи: {stats['waste_percent']}%\n\n"
            f"Розподіл по листах:\n",
        )
        for i, sheet in enumerate(self.nesting.sheets):
            self.detail_text.insert("end", f"\nЛист {i+1}: {len(sheet)} деталей\n")
            for p in sheet:
                self.detail_text.insert(
                    "end", f"  • {p.name} ({p.width:.0f}x{p.height:.0f}) @ ({p.x:.0f},{p.y:.0f})\n"
                )
        self.detail_text.config(state="disabled")

        self.draw_nesting()
        messagebox.showinfo("Готово", f"Розкрій виконано!\nПотрібно листів: {sheets_needed}")

    def reset_results(self):
        self.res_sheets.config(text="—")
        self.res_util.config(text="—")
        self.res_waste.config(text="—")
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.config(state="disabled")

    # ═══════════════════════════════════════════════════════
    #  МАЛЮВАННЯ НА CANVAS
    # ═══════════════════════════════════════════════════════
    def _draw_placeholder(self):
        """Малює тестовий фон при старті"""
        print("[CamDuct] _draw_placeholder called")
        self.canvas.delete("all")
        self.canvas.create_rectangle(50, 50, 250, 170, outline="#bdc3c7", fill="#ecf0f1", width=2)
        self.canvas.create_text(
            150, 100, text="Область розкрою", font=("Segoe UI", 16, "bold"), fill="#7f8c8d"
        )
        self.canvas.create_text(
            150,
            125,
            text="Додайте деталі → натисніть РОЗКРИТИ",
            font=("Segoe UI", 11),
            fill="#95a5a6",
        )
        self.canvas.config(scrollregion=(0, 0, 300, 200))

    def draw_nesting(self):
        print(
            f"[CamDuct] draw_nesting called. nesting: {self.nesting is not None}, current_sheet: {self.current_sheet}"
        )
        self.canvas.delete("all")
        self.scale = self.scale_var.get()
        self.scale_label.config(text=f"{self.scale:.2f} px/мм")

        if not self.nesting or not self.nesting.sheets:
            # Тестовий фон якщо немає розкрою
            self.canvas.create_rectangle(
                50, 50, 200, 150, outline="#bdc3c7", fill="#ecf0f1", width=2
            )
            self.canvas.create_text(
                125, 100, text="Область розкрою", font=("Segoe UI", 14), fill="#7f8c8d"
            )
            self.canvas.create_text(
                125,
                120,
                text="Додайте деталі → натисніть РОЗКРИТИ",
                font=("Segoe UI", 10),
                fill="#95a5a6",
            )
            self.canvas.config(scrollregion=(0, 0, 300, 200))
            return

        if self.current_sheet >= len(self.nesting.sheets):
            self.current_sheet = 0

        sw = self.nesting.sheet_w
        sh = self.nesting.sheet_h
        s = self.scale

        # Малюємо лист
        w_px = int(sw * s)
        h_px = int(sh * s)
        self.canvas.create_rectangle(
            10, 10, 10 + w_px, 10 + h_px, outline="#2c3e50", width=2, fill="#ecf0f1"
        )
        self.canvas.create_text(
            10 + w_px / 2, 5, text=f"{sw} x {sh} мм", font=("Segoe UI", 10, "bold"), fill="#2c3e50"
        )

        # Сітка
        grid_step = 100  # мм
        step_px = int(grid_step * s)
        for x in range(0, w_px + 1, step_px):
            self.canvas.create_line(10 + x, 10, 10 + x, 10 + h_px, fill="#bdc3c7", dash=(2, 4))
        for y in range(0, h_px + 1, step_px):
            self.canvas.create_line(10, 10 + y, 10 + w_px, 10 + y, fill="#bdc3c7", dash=(2, 4))

        # Малюємо деталі
        sheet = self.nesting.sheets[self.current_sheet]
        for p in sheet:
            x1 = 10 + int(p.x * s)
            y1 = 10 + int(p.y * s)
            x2 = x1 + int(p.width * s)
            y2 = y1 + int(p.height * s)
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", width=1, fill=p.color)
            # Підпис
            if p.width * s > 40 and p.height * s > 20:
                self.canvas.create_text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    text=p.name[:12],
                    font=("Segoe UI", 7),
                    fill="white",
                )
            # Розміри
            if p.width * s > 60:
                self.canvas.create_text(
                    (x1 + x2) / 2, y2 + 10, text=f"{p.width:.0f}", font=("Segoe UI", 7), fill="#333"
                )
            if p.height * s > 40:
                self.canvas.create_text(
                    x2 + 12,
                    (y1 + y2) / 2,
                    text=f"{p.height:.0f}",
                    font=("Segoe UI", 7),
                    fill="#333",
                    angle=90,
                )

        # Оновлюємо scrollregion
        self.canvas.config(scrollregion=(0, 0, 20 + w_px, 20 + h_px))

    def on_sheet_nav(self, event=None):
        idx = self.sheet_nav.current()
        if idx >= 0:
            self.current_sheet = idx
            self.draw_nesting()

    def prev_sheet(self):
        if self.nesting and self.current_sheet > 0:
            self.current_sheet -= 1
            self.sheet_nav.current(self.current_sheet)
            self.draw_nesting()

    def next_sheet(self):
        if self.nesting and self.current_sheet < len(self.nesting.sheets) - 1:
            self.current_sheet += 1
            self.sheet_nav.current(self.current_sheet)
            self.draw_nesting()

    # ═══════════════════════════════════════════════════════
    #  ЗБЕРЕГТИ / ЕКСПОРТ
    # ═══════════════════════════════════════════════════════
    def save_nesting(self):
        if not self.nesting:
            messagebox.showwarning("Увага", "Спочатку виконайте розкрій!")
            return
        data = {
            "date": datetime.now().isoformat(),
            "sheet_size": [self.nesting.sheet_w, self.nesting.sheet_h],
            "kerf": self.nesting.kerf,
            "stats": self.nesting.get_stats(),
            "parts": [
                {
                    "name": p.name,
                    "type": p.part_type,
                    "width": p.width,
                    "height": p.height,
                    "qty": p.quantity,
                }
                for p in self.parts
            ],
            "sheets": [
                [
                    {
                        "name": p.name,
                        "x": p.x,
                        "y": p.y,
                        "w": p.width,
                        "h": p.height,
                        "color": p.color,
                    }
                    for p in sheet
                ]
                for sheet in self.nesting.sheets
            ],
        }
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile=f"nesting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Готово", f"Розкрій збережено:\n{filepath}")

    def export_csv(self):
        if not self.nesting:
            messagebox.showwarning("Увага", "Спочатку виконайте розкрій!")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"nesting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not filepath:
            return
        import csv

        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Лист", "Деталь", "Тип", "X", "Y", "Ширина", "Висота", "Площа м²"])
            for i, sheet in enumerate(self.nesting.sheets, 1):
                for p in sheet:
                    writer.writerow(
                        [
                            i,
                            p.name,
                            p.part_type,
                            p.x,
                            p.y,
                            p.width,
                            p.height,
                            round(p.width * p.height / 1_000_000, 4),
                        ]
                    )
            stats = self.nesting.get_stats()
            writer.writerow([])
            writer.writerow(["Статистика", "", "", "", "", "", "", ""])
            writer.writerow(["Листів", stats["sheets_count"], "", "", "", "", "", ""])
            writer.writerow(
                ["Використання %", stats["utilization_percent"], "", "", "", "", "", ""]
            )
        messagebox.showinfo("Готово", f"CSV експортовано:\n{filepath}")
