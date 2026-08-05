#!/usr/bin/env python3
"""
Базовий клас для всіх вкладок VentCompany GUI.
"""

import tkinter as tk
from tkinter import messagebox, ttk


class BaseTab(tk.Frame):
    """Базовий клас для кожної вкладки."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.colors = app.colors
        self.root = app.root
        self.configure(bg=self.colors["bg"])
        self.style = ttk.Style()
        self.setup_ui()

    def setup_ui(self):
        """Перевизначіть у нащадках."""
        raise NotImplementedError

    def refresh(self):
        """Викликається при кожному відкритті вкладки."""
        pass

    def show_message(self, title, message):
        messagebox.showinfo(title, message)

    def show_error(self, title, message):
        messagebox.showerror(title, message)

    def ask_confirmation(self, title, message):
        return messagebox.askyesno(title, message)

    def set_status(self, text):
        self.app.status_label.config(text=text)

    def _parse_float(self, value_str, field_name, allow_empty=True):
        raw = (value_str or "").strip().replace(",", ".")
        if allow_empty and not raw:
            return 0.0
        try:
            return float(raw)
        except ValueError as err:
            raise ValueError(
                f"Невірне значення у полі '{field_name}': '{value_str}'. Введіть число."
            ) from err
