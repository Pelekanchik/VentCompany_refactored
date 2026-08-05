#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Головне вікно VentCompany.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from ventilation_company.database import init_database

# Вкладки
from .projects_tab import ProjectsTab
from .components_tab import ComponentsTab
from .works_tab import WorksTab
from .materials_tab import MaterialsTab
from .accounting_tab import AccountingTab
from .archive_tab import ArchiveTab
from .analytics_tab import AnalyticsTab
from .camduct_tab import CamDuctTab
from .cad_tab import CADTab
from .price_list_tab import PriceListTab


class VentilationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ВЕНТИЛЯЦІЙНА ВИРОБНИЧА ФІРМА — Система управління")
        self.root.geometry("1920x1080")
        self.root.state("zoomed")
        self.root.minsize(1400, 900)

        self.themes = {
            "Світла": {"bg": "#f0f0f0", "fg": "#333333", "sidebar": "#2c3e50",
                       "sidebar_fg": "white", "accent": "#3498db", "card": "white"},
            "Темна": {"bg": "#1a1a2e", "fg": "#eaeaea", "sidebar": "#16213e",
                      "sidebar_fg": "#eaeaea", "accent": "#e94560", "card": "#0f3460"},
            "Зелена": {"bg": "#e8f5e9", "fg": "#1b5e20", "sidebar": "#2e7d32",
                       "sidebar_fg": "white", "accent": "#66bb6a", "card": "#c8e6c9"},
            "Синя": {"bg": "#e3f2fd", "fg": "#0d47a1", "sidebar": "#1565c0",
                      "sidebar_fg": "white", "accent": "#42a5f5", "card": "#bbdefb"},
            "Помаранчева": {"bg": "#fff3e0", "fg": "#e65100", "sidebar": "#ef6c00",
                             "sidebar_fg": "white", "accent": "#ff9800", "card": "#ffe0b2"},
        }
        self.current_theme = "Світла"
        self.colors = self.themes[self.current_theme]

        init_database()
        self.create_menu()
        self.create_sidebar()
        self.create_content_area()
        self.show_tab("projects", "УПРАВЛІННЯ ПРОЕКТАМИ ВЕНТИЛЯЦІЇ")

    def apply_theme(self):
        c = self.colors
        self.root.configure(bg=c["bg"])
        self.sidebar_frame.configure(bg=c["sidebar"])
        self.content_frame.configure(bg=c["bg"])
        for btn in self.sidebar_buttons:
            btn.configure(bg=c["sidebar"], fg=c["sidebar_fg"],
                         activebackground=c["accent"], activeforeground="white")
        self.header_label.configure(bg=c["bg"], fg=c["fg"])
        for frame in self.tabs.values():
            frame.configure(bg=c["bg"])
            for child in frame.winfo_children():
                if isinstance(child, tk.Frame):
                    child.configure(bg=c["bg"])
                elif isinstance(child, tk.Label):
                    child.configure(bg=c["bg"], fg=c["fg"])
                elif isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, tk.Label):
                            subchild.configure(bg=c["bg"], fg=c["fg"])

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        theme_menu = tk.Menu(menubar, tearoff=0)
        for theme_name in self.themes.keys():
            theme_menu.add_command(label=theme_name,
                                   command=lambda t=theme_name: self.change_theme(t))
        menubar.add_cascade(label="Тема", menu=theme_menu)

        action_menu = tk.Menu(menubar, tearoff=0)
        action_menu.add_command(label="Повний звіт", command=self.generate_full_report)
        action_menu.add_command(label="Аналітична панель", command=self.show_analytics)
        action_menu.add_separator()
        action_menu.add_command(label="Вихід", command=self.root.quit)
        menubar.add_cascade(label="Дії", menu=action_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Про програму", command=self.show_about)
        menubar.add_cascade(label="Довідка", menu=help_menu)

    def change_theme(self, theme_name):
        self.current_theme = theme_name
        self.colors = self.themes[theme_name]
        self.apply_theme()
        if hasattr(self, '_current_tab_name') and self._current_tab_name in self.tabs:
            tab = self.tabs[self._current_tab_name]
            if hasattr(tab, 'refresh'):
                tab.refresh()
        messagebox.showinfo("Тему змінено", f"Встановлено тему: {theme_name}")

    def create_sidebar(self):
        c = self.colors
        self.sidebar_frame = tk.Frame(self.root, bg=c["sidebar"], width=250)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)

        logo_label = tk.Label(self.sidebar_frame, text="ВЕНТ-ФІРМА",
                              bg=c["sidebar"], fg=c["sidebar_fg"],
                              font=("Arial", 20, "bold"), pady=20)
        logo_label.pack(fill=tk.X)

        tk.Frame(self.sidebar_frame, bg=c["accent"], height=2).pack(fill=tk.X, padx=10)

        self.sidebar_buttons = []
        tabs_config = [
            ("Проекти", "projects", "УПРАВЛІННЯ ПРОЕКТАМИ ВЕНТИЛЯЦІЇ"),
            ("Вироби", "components", "КАТАЛОГ ВИРОБІВ ТА КОМПОНЕНТІВ"),
            ("Роботи", "works", "УПРАВЛІННЯ РОБОТАМИ"),
            ("Бухгалтерія", "accounting", "БУХГАЛТЕРСЬКИЙ ОБЛІК"),
            ("Архів", "archive", "АРХІВ ПРОЕКТІВ"),
            ("Аналітика", "analytics", "АНАЛІТИЧНА ПАНЕЛЬ"),
            ("Розкрій листа", "camduct", "РОЗКРІЙ ЛИСТОВОГО МЕТАЛУ"),
            ("Креслення", "cad", "2D CAD — КРЕСЛЕННЯ ДЕТАЛЕЙ"),
            ("Прайс-лист", "price_list", "ПРАЙС-ЛИСТ ВИРОБІВ"),
        ]

        for text, tab_id, title in tabs_config:
            btn = tk.Button(self.sidebar_frame, text=text, bg=c["sidebar"],
                           fg=c["sidebar_fg"], font=("Arial", 12),
                           activebackground=c["accent"], activeforeground="white",
                           bd=0, pady=12, cursor="hand2",
                           command=lambda tid=tab_id, ttl=title: self.show_tab(tid, ttl))
            btn.pack(fill=tk.X, padx=10, pady=2)
            self.sidebar_buttons.append(btn)

        tk.Frame(self.sidebar_frame, bg=c["accent"], height=2).pack(fill=tk.X, padx=10, pady=10)

        self.status_label = tk.Label(self.sidebar_frame, text="Система активна",
                                     bg=c["sidebar"], fg=c["sidebar_fg"],
                                     font=("Arial", 9), pady=10)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def create_content_area(self):
        c = self.colors
        self.content_frame = tk.Frame(self.root, bg=c["bg"])
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Заголовок прибрано для економії місця
        self.header_label = tk.Label(self.content_frame, text="", bg=c["bg"], height=1)
        self.header_label.pack(fill=tk.X)

        self.tabs_container = tk.Frame(self.content_frame, bg=c["bg"])
        self.tabs_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.tabs = {}
        self._tab_classes = {
            "projects": ProjectsTab,
            "components": ComponentsTab,
            "works": WorksTab,
            "materials": MaterialsTab,
            "accounting": AccountingTab,
            "archive": ArchiveTab,
            "analytics": AnalyticsTab,
            "camduct": CamDuctTab,
            "cad": CADTab,
            "price_list": PriceListTab,
        }

    def show_tab(self, tab_name, title):
        # Заголовок прибрано
        self._current_tab_name = tab_name

        for name, frame in self.tabs.items():
            frame.pack_forget()

        if tab_name not in self.tabs:
            TabClass = self._tab_classes[tab_name]
            self.tabs[tab_name] = TabClass(self.tabs_container, self)

        tab = self.tabs[tab_name]
        tab.pack(fill=tk.BOTH, expand=True)
        if hasattr(tab, 'refresh'):
            tab.refresh()

        self.status_label.config(text=f"Активна вкладка: {title}")

    def generate_full_report(self):
        try:
            from ventilation_company.archive.reports import ReportGenerator
            gen = ReportGenerator()
            report = gen.generate_full_report()
            messagebox.showinfo("Звіт згенеровано", f"Звіт збережено:\n{report}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося згенерувати звіт: {e}")

    def show_analytics(self):
        self.show_tab("analytics", "АНАЛІТИЧНА ПАНЕЛЬ")

    def show_about(self):
        messagebox.showinfo("Про програму",
            "VentCompany v2.0\n"
            "Система управління вентиляційною фірмою\n\n"
            "Можливості:\n"
            "• Управління проектами\n"
            "• Калькуляція витрат\n"
            "• Розкрій листового металу\n"
            "• 2D CAD редактор\n"
            "• Архів та аналітика")
