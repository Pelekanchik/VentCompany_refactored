"""
Модуль зберігання та архівування
"""
import os
from datetime import datetime
from ventilation_company.config import ARCHIVE_DIR, PROJECTS_DIR
from ventilation_company.database import execute_query
from ventilation_company.utils.archive_manager import ArchiveManager


class ArchiveStorage:
    def __init__(self):
        self.archive_manager = ArchiveManager()
        os.makedirs(ARCHIVE_DIR, exist_ok=True)

    def archive_project(self, project_id, project_number, source_files=None):
        if source_files is None:
            source_files = self._find_project_files(project_number)
        archive_path = self.archive_manager.create_project_archive(project_number, source_files)
        file_size = os.path.getsize(archive_path)
        query = """
            INSERT INTO archive (archive_name, project_id, file_path, file_size, created_at, archive_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        execute_query(query, (
            os.path.basename(archive_path), project_id, archive_path, file_size,
            datetime.now().isoformat(), "project"
        ))
        execute_query("UPDATE projects SET status = 'archived' WHERE id = ?", (project_id,))
        print(f"Проєкт {project_number} архівовано")
        return archive_path

    def _find_project_files(self, project_number):
        files = []
        json_file = os.path.join(PROJECTS_DIR, f"{project_number}.json")
        if os.path.exists(json_file):
            files.append(json_file)
        spec_file = os.path.join(PROJECTS_DIR, f"{project_number}_spec.txt")
        if os.path.exists(spec_file):
            files.append(spec_file)
        summary_file = os.path.join(PROJECTS_DIR, f"{project_number}_summary.txt")
        if os.path.exists(summary_file):
            files.append(summary_file)
        return files

    def list_archives(self):
        query = """
            SELECT a.id, a.archive_name, p.project_number, p.name, a.created_at, a.file_size
            FROM archive a
            LEFT JOIN projects p ON a.project_id = p.id
            ORDER BY a.created_at DESC
        """
        return execute_query(query)

    def print_archives(self):
        archives = self.list_archives()
        print("\n" + "=" * 90)
        print("АРХІВ ПРОЄКТІВ".center(90))
        print("=" * 90)
        print(f"{'ID':<5} {'Назва архіву':<35} {'Проєкт':<20} {'Дата':<12} {'Розмір':<10}")
        print("-" * 90)
        for arch in archives:
            size_kb = arch[5] / 1024 if arch[5] else 0
            print(f"{arch[0]:<5} {arch[1]:<35} {str(arch[2]):<20} {arch[4][:10]:<12} {size_kb:>8.1f} КБ")
        print("=" * 90)
        print(f"  Всього архівів: {len(archives)}")
        print("=" * 90)

    def restore_project(self, archive_path, extract_to=None):
        if extract_to is None:
            extract_to = os.path.join(PROJECTS_DIR, "restored")
        extracted = self.archive_manager.extract_archive(archive_path, extract_to)
        print(f"Проєкт відновлено: {extracted}")
        return extracted

    def delete_archive(self, archive_id):
        query = "SELECT file_path FROM archive WHERE id = ?"
        row = execute_query(query, (archive_id,), fetch_one=True)
        if row and os.path.exists(row[0]):
            os.remove(row[0])
        execute_query("DELETE FROM archive WHERE id = ?", (archive_id,))
        print(f"Архів ID {archive_id} видалено")
