#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Вкладка \"Архів\"."""

import tkinter as tk
from tkinter import ttk

from .base_tab import BaseTab
from ventilation_company.archive.storage import ArchiveStorage


class ArchiveTab(BaseTab):
    def setup_ui(self):
        c = self.colors
        tk.Label(self, text="АРХІВ ПРОЕКТІВ", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 18, "bold")).pack(pady=15)

        btn_frame = tk.Frame(self, bg=c["bg"])
        btn_frame.pack(fill=tk.X, pady=10)

        tk.Button(btn_frame, text="🔄 Оновити", bg=c["accent"], fg="white",
                  font=("Arial", 11), command=self.refresh).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📦 Архівувати проект", bg="#9b59b6", fg="white",
                  font=("Arial", 11), command=self.archive_selected).pack(side=tk.LEFT, padx=5)

        columns = ("ID", "Назва архіву", "Проект", "Дата", "Розмір (КБ)")
        self.archive_tree = ttk.Treeview(self, columns=columns, show="headings", height=20)
        for col in columns:
            self.archive_tree.heading(col, text=col)
            self.archive_tree.column(col, width=180)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.archive_tree.yview)
        self.archive_tree.configure(yscrollcommand=scrollbar.set)

        self.archive_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh()

    def refresh(self):
        for item in self.archive_tree.get_children():
            self.archive_tree.delete(item)
        storage = ArchiveStorage()
        archives = storage.list_archives()
        for a in archives:
            size_kb = round(a[5] / 1024, 1) if a[5] else 0
            self.archive_tree.insert("", tk.END, values=(
                a[0], a[1], f"{a[2]} — {a[3]}", a[4][:10], size_kb
            ))

    def archive_selected(self):
        self.show_message("Архів", "Функція архівації — додайте вибір проекту")
