#!/usr/bin/env python3
"""Вкладка \"Розкрій листа\" — CamDuct."""

import tkinter as tk

from ventilation_company.camduct_editor import CamDuctEditorFrame

from .base_tab import BaseTab


class CamDuctTab(BaseTab):
    def setup_ui(self):
        c = self.colors
        try:
            self.camduct_editor = CamDuctEditorFrame(self, colors=self.colors)
            self.camduct_editor.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            tk.Label(
                self, text=f"Помилка CamDuct: {e}", bg=c["bg"], fg="#e74c3c", font=("Arial", 14)
            ).pack(expand=True)

    def refresh(self):
        pass
