#!/usr/bin/env python3
"""Вкладка "Прайс-лист"."""


from ventilation_company.price_list_tab import PriceListTab as OriginalPriceListTab

from .base_tab import BaseTab


class PriceListTab(BaseTab):
    def setup_ui(self):
        # Передаємо правильно: root=головне вікно, notebook=сам BaseTab (який є фреймом у Notebook)
        self.original = OriginalPriceListTab(self.root, self, colors=self.colors)

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self.setup_ui()
