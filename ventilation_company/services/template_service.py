"""
Сервіс шаблонів розрахунків
"""

from typing import Any

from ventilation_company.database.repositories.template_repo import TemplateRepo


class TemplateService:
    """Сервіс для управління шаблонами розрахунків."""

    @staticmethod
    def get_all_templates() -> list[dict[str, Any]]:
        """Повертає всі шаблони."""
        rows = TemplateRepo.get_all()
        return [dict(row) for row in rows]

    @staticmethod
    def get_template(template_id: int) -> dict[str, Any] | None:
        """Повертає шаблон за ID."""
        row = TemplateRepo.get_by_id(template_id)
        return dict(row) if row else None

    @staticmethod
    def create_template(name: str, description: str = "", items_data: list[dict] = None) -> int:
        """Створює новий шаблон."""
        return TemplateRepo.add(name, description, items_data)

    @staticmethod
    def update_template(template_id: int, **kwargs) -> None:
        """Оновлює шаблон."""
        TemplateRepo.update(template_id, **kwargs)

    @staticmethod
    def delete_template(template_id: int) -> None:
        """Видаляє шаблон."""
        TemplateRepo.delete(template_id)

    @staticmethod
    def apply_template(
        template_id: int, client_name: str = "", client_phone: str = ""
    ) -> int | None:
        """Застосовує шаблон — створює новий розрахунок на основі шаблону."""
        from ventilation_company.database.repositories.calc_repo import CalcRepo

        template = TemplateRepo.get_by_id(template_id)
        if not template:
            return None

        import json

        calc_id = CalcRepo.add_calculation(client_name, client_phone)

        items_data = json.loads(template["items_data"]) if template["items_data"] else []
        for item in items_data:
            CalcRepo.add_item(
                calculation_id=calc_id,
                subtype_id=item.get("subtype_id", 0),
                material_id=item.get("material_id", 0),
                size_params=item.get("size_params", {}),
                quantity=item.get("quantity", 1),
                area=item.get("area", 0.0),
            )

        return calc_id
