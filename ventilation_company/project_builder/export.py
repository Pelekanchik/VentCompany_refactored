"""
Модуль експорту проекту
"""
import os
from ventilation_company.config import REPORTS_DIR
from ventilation_company.utils.archive_manager import ArchiveManager


class ProjectExporter:
    def __init__(self, project):
        self.project = project
        self.exported_files = []

    def export_all(self, include_archive=True):
        print(f"\nEksport proektu {self.project.project_number}...")
        json_file = self.export_json()
        self.exported_files.append(json_file)
        from project_builder.specifications import SpecificationBuilder
        spec_builder = SpecificationBuilder(self.project)
        txt_file = spec_builder.export_to_txt()
        self.exported_files.append(txt_file)
        if include_archive:
            archive_mgr = ArchiveManager()
            archive_path = archive_mgr.create_project_archive(
                self.project.project_number,
                self.exported_files
            )
            self.exported_files.append(archive_path)
        print(f"Eksport zaversheno! Stvoreno {len(self.exported_files)} fajliv")
        return self.exported_files

    def export_json(self, filepath=None):
        return self.project.export_to_json(filepath)

    def export_summary(self):
        summary = self.project.get_summary()
        filepath = os.path.join(REPORTS_DIR, f"{self.project.project_number}_summary.txt")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("PIDSUMOK PROEKTU\n")
            f.write("=" * 50 + "\n")
            f.write(f"Nomer: {summary['project_number']}\n")
            f.write(f"Nazva: {summary['name']}\n")
            f.write(f"Zamovnyk: {summary['client']}\n")
            f.write(f"Typ: {summary['ventilation_type']}\n\n")
            f.write(f"Vartist komplektuuchykh: {summary['components_cost']:.2f} hrn\n")
            f.write(f"Vartist materialiv: {summary['materials_cost']:.2f} hrn\n")
            f.write(f"Vartist robot: {summary['works_cost']:.2f} hrn\n")
            f.write("=" * 50 + "\n")
            f.write(f"Bazova vartist: {summary['total_base']:.2f} hrn\n")
        print(f"Pidsumok eksportovano: {filepath}")
        return filepath
