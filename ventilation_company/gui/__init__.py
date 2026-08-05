#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль графічного інтерфейсу VentCompany.
"""

import tkinter as tk
from .main_window import VentilationApp


def main():
    """Точка входу для GUI."""
    root = tk.Tk()
    app = VentilationApp(root)
    root.mainloop()


__all__ = ["VentilationApp", "main"]
