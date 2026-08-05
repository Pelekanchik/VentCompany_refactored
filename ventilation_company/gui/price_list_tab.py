#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Вкладка \"Прайс-лист\"."""

import tkinter as tk

from .base_tab import BaseTab
from ventilation_company.price_list_tab import PriceListTab as OriginalPriceListTab


class PriceListTab(BaseTab):
    def setup_ui(self):
        c = self.colors
        OriginalPriceListTab(self, self.root, colors=self.colors)

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self.setup_ui()
