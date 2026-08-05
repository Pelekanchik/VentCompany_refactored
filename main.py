#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ВЕНТИЛЯЦІЙНА ВИРОБНИЧА ФІРМА
Запуск: python main.py        → GUI режим
        python main.py --cli  → Консольний режим
"""

import sys


def run_gui():
    """Функція для запуску GUI."""
    try:
        from ventilation_company.gui import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"Помилка запуску GUI: {e}")
        print("Спробуйте: pip install tk")
        raise


def run_cli():
    """Функція для запуску CLI."""
    from ventilation_company.main_cli import main as cli_main
    cli_main()


if __name__ == "__main__":
    if "--cli" in sys.argv or "-c" in sys.argv:
        run_cli()
    else:
        run_gui()
