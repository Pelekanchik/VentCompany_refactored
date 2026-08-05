#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Вкладка \"Креслення\" — 2D CAD."""

import tkinter as tk

from .base_tab import BaseTab
from ventilation_company.cad_editor import CADEditorFrame


class CADTab(BaseTab):
    def setup_ui(self):
        c = self.colors
        tk.Label(self, text="2D CAD — КРЕСЛЕННЯ ДЕТАЛЕЙ", bg=c["bg"], fg=c["fg"],
                 font=("Arial", 14, "bold")).pack(fill=tk.X, pady=(4, 2))

        cad_frame = tk.Frame(self, bg=c["bg"])
        cad_frame.pack(fill=tk.BOTH, expand=True)

        self.cad_editor = CADEditorFrame(cad_frame, colors=self.colors)
        self.cad_editor.pack(fill=tk.BOTH, expand=True)
