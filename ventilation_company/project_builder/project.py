"""
Project Builder — бізнес-логіка управління проєктами.
Модель Project винесено в ventilation_company.models.project
"""

import os

from ventilation_company.config import PROJECTS_DIR
from ventilation_company.database import execute_query
from ventilation_company.models.project import Project


class ProjectService:
    """Сервіс для роботи з проєктами (CRUD + бізнес-логіка)."""

    @staticmethod
    def create(
        name: str,
        client: str = "",
        address: str = "",
        ventilation_type: str = "припливна",
        air_flow: float = 0,
        pressure: float = 0,
    ) -> Project:
        """Створює новий проєкт."""
        project = Project(
            name=name,
            client=client,
            address=address,
            ventilation_type=ventilation_type,
            air_flow=air_flow,
            pressure=pressure,
        )
        return project

    @staticmethod
    def save_to_db(project: Project) -> int:
        """Зберігає проєкт у базу даних."""
        valid, errors = project.validate()
        if not valid:
            print("Помилки валідації:")
            for err in errors:
                print(f"   - {err}")
            return 0

        query = """
            INSERT INTO projects
            (project_number, name, client, address, ventilation_type,
             air_flow, pressure, created_at, updated_at, status, total_area, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            project.project_number,
            project.name,
            project.client,
            project.address,
            project.ventilation_type,
            project.air_flow,
            project.pressure,
            project.created_at,
            project.updated_at,
            project.status,
            project.total_area,
            project.notes,
        )
        project.id = execute_query(query, params)
        print(f"Проєкт збережено в БД (ID: {project.id})")

        # Зберігаємо компоненти
        for comp in project._components:
            execute_query(
                """INSERT INTO project_components
                   (project_id, component_name, quantity, unit, unit_price, total_price)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    project.id,
                    comp["name"],
                    comp["quantity"],
                    comp["unit"],
                    comp["unit_price"],
                    comp["total_price"],
                ),
            )

        # Зберігаємо матеріали
        for mat in project._materials:
            execute_query(
                """INSERT INTO project_materials
                   (project_id, material_name, quantity, unit, unit_price, total_price)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    project.id,
                    mat["name"],
                    mat["quantity"],
                    mat["unit"],
                    mat["unit_price"],
                    mat["total_price"],
                ),
            )

        # Зберігаємо роботи
        for work in project._works:
            execute_query(
                """INSERT INTO project_works
                   (project_id, work_name, quantity, unit, unit_price, total_price)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    project.id,
                    work["name"],
                    work["quantity"],
                    work["unit"],
                    work["unit_price"],
                    work["total_price"],
                ),
            )

        return project.id

    @staticmethod
    def update_in_db(project: Project) -> bool:
        """Оновлює проєкт у базі даних."""
        if project.id is None:
            print("Проєкт не збережено в БД")
            return False

        project.updated_at = __import__("datetime").datetime.now().isoformat()
        query = """
            UPDATE projects SET
                name = ?, client = ?, address = ?, ventilation_type = ?,
                air_flow = ?, pressure = ?, updated_at = ?, status = ?,
                total_area = ?, notes = ?
            WHERE id = ?
        """
        params = (
            project.name,
            project.client,
            project.address,
            project.ventilation_type,
            project.air_flow,
            project.pressure,
            project.updated_at,
            project.status,
            project.total_area,
            project.notes,
            project.id,
        )
        execute_query(query, params)
        print("Проєкт оновлено в БД")
        return True

    @staticmethod
    def load_from_db(project_id: int) -> Project:
        """Завантажує проєкт з бази даних."""
        query = "SELECT * FROM projects WHERE id = ?"
        row = execute_query(query, (project_id,), fetch_one=True)
        if row is None:
            return None

        project = Project(
            name=row[2],
            client=row[3] or "",
            address=row[4] or "",
            ventilation_type=row[5],
            air_flow=row[6] or 0,
            pressure=row[7] or 0,
            project_number=row[1],
        )
        project.id = row[0]
        project.created_at = row[8]
        project.updated_at = row[9]
        project.status = row[10]
        project.total_area = row[11] or 0
        project.notes = row[12] or ""

        # Компоненти
        for comp in execute_query(
            "SELECT * FROM project_components WHERE project_id = ?", (project_id,)
        ):
            project._components.append(
                {
                    "name": comp[2],
                    "quantity": comp[3],
                    "unit": comp[4],
                    "unit_price": comp[5],
                    "total_price": comp[6],
                }
            )

        # Матеріали
        for mat in execute_query(
            "SELECT * FROM project_materials WHERE project_id = ?", (project_id,)
        ):
            project._materials.append(
                {
                    "name": mat[2],
                    "quantity": mat[3],
                    "unit": mat[4],
                    "unit_price": mat[5],
                    "total_price": mat[6],
                }
            )

        # Роботи
        for work in execute_query(
            "SELECT * FROM project_works WHERE project_id = ?", (project_id,)
        ):
            project._works.append(
                {
                    "name": work[2],
                    "quantity": work[3],
                    "unit": work[4],
                    "unit_price": work[5],
                    "total_price": work[6],
                }
            )

        return project

    @staticmethod
    def list_all():
        """Повертає список усіх проєктів."""
        query = """
            SELECT id, project_number, name, client, status, created_at
            FROM projects ORDER BY created_at DESC
        """
        return execute_query(query)

    @staticmethod
    def export_to_json(project: Project, filepath: str = None) -> str:
        """Експортує проєкт у JSON."""
        if filepath is None:
            filepath = os.path.join(PROJECTS_DIR, f"{project.project_number}.json")
        data = project.to_dict()
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            __import__("json").dump(data, f, ensure_ascii=False, indent=2)
        print(f"Проєкт експортовано: {filepath}")
        return filepath
