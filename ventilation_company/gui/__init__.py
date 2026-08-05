#!/usr/bin/env python3
"""
Модуль графічного інтерфейсу VentCompany.
"""

import tkinter as tk

from .main_window import VentilationApp


def main():
    """Точка входу для GUI."""
    root = tk.Tk()
    VentilationApp(root)
    root.mainloop()


__all__ = ["VentilationApp", "main"]
