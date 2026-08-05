#!/usr/bin/env python3
"""Вкладка \"Аналітика\"."""

import tkinter as tk

from ventilation_company.archive.analytics import ProductionAnalytics

from .base_tab import BaseTab


class AnalyticsTab(BaseTab):
    def setup_ui(self):
        c = self.colors
        tk.Label(
            self, text="АНАЛІТИЧНА ПАНЕЛЬ", bg=c["bg"], fg=c["fg"], font=("Arial", 18, "bold")
        ).pack(pady=15)

        frame = tk.Frame(self, bg=c["bg"], padx=50)
        frame.pack(fill=tk.BOTH, expand=True)

        analytics = ProductionAnalytics()
        projects = analytics.get_projects_stats()
        financial = analytics.get_financial_stats()

        by_status = projects.get("by_status", {})
        blocks = [
            (
                "📊 Проекти",
                [
                    f"Всього: {projects.get('total_projects', 0)}",
                    f"Унікальних замовників: {projects.get('total_clients', 0)}",
                    f"Активні: {by_status.get('active', 0)}",
                    f"Завершені: {by_status.get('completed', 0)}",
                    f"Архівовані: {by_status.get('archived', 0)}",
                ],
            ),
            (
                "💰 Фінанси",
                [
                    f"Дохід: {financial.get('total_revenue', 0):.2f} грн",
                    f"Витрати: {financial.get('total_cost', 0):.2f} грн",
                    f"Прибуток: {financial.get('total_profit', 0):.2f} грн",
                    f"Середня рентабельність: {financial.get('avg_profit_margin', 0):.2f}%",
                ],
            ),
        ]

        for title, lines in blocks:
            self._create_info_block(frame, title, lines)

    def _create_info_block(self, parent, title, data_lines):
        c = self.colors
        block = tk.Frame(parent, bg=c["card"], bd=1, relief="solid", padx=20, pady=15)
        block.pack(fill=tk.X, pady=10)
        tk.Label(block, text=title, bg=c["card"], fg=c["fg"], font=("Arial", 14, "bold")).pack(
            anchor="w"
        )
        for line in data_lines:
            tk.Label(block, text=f"  • {line}", bg=c["card"], fg=c["fg"], font=("Arial", 11)).pack(
                anchor="w", pady=2
            )
