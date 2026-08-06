#!/usr/bin/env python3
"""Вкладка "Креслення" — 2D CAD + FreeCAD."""

import tkinter as tk

from ventilation_company.cad_editor import CADEditorFrame

try:
    from ventilation_company.freecad_exporter import FREECAD_AVAILABLE
except ImportError:
    FREECAD_AVAILABLE = False

from .base_tab import BaseTab


class CADTab(BaseTab):
    def setup_ui(self):
        c = self.colors

        # Заголовок + статус FreeCAD
        header = tk.Frame(self, bg=c["bg"])
        header.pack(fill=tk.X, pady=(4, 2))

        tk.Label(
            header,
            text="2D CAD — КРЕСЛЕННЯ ДЕТАЛЕЙ",
            bg=c["bg"],
            fg=c["fg"],
            font=("Arial", 14, "bold"),
        ).pack(side=tk.LEFT, padx=10)

        fc_color = "#27ae60" if FREECAD_AVAILABLE else "#e74c3c"
        fc_text = "✅ FreeCAD" if FREECAD_AVAILABLE else "❌ FreeCAD не встановлено"
        tk.Label(header, text=fc_text, bg=c["bg"], fg=fc_color, font=("Arial", 10, "bold")).pack(
            side=tk.RIGHT, padx=10
        )

        # CAD-редактор
        cad_frame = tk.Frame(self, bg=c["bg"])
        cad_frame.pack(fill=tk.BOTH, expand=True)

        self.cad_editor = CADEditorFrame(cad_frame, colors=self.colors)
        self.cad_editor.pack(fill=tk.BOTH, expand=True)
