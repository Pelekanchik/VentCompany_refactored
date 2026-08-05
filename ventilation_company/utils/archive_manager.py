"""
Менеджер архівів
"""

import os
import shutil
import zipfile
from datetime import datetime

from ventilation_company.config import ARCHIVE_DIR


class ArchiveManager:
    def __init__(self, archive_dir=None):
        self.archive_dir = archive_dir or ARCHIVE_DIR
        os.makedirs(self.archive_dir, exist_ok=True)

    def create_project_archive(self, project_number, source_files, archive_name=None):
        if archive_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"{project_number}_{timestamp}.zip"
        archive_path = os.path.join(self.archive_dir, archive_name)
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in source_files:
                if os.path.exists(file_path):
                    arcname = os.path.basename(file_path)
                    zf.write(file_path, arcname)
                    print(f"  DODANO: {arcname}")
                else:
                    print(f"  PROPUSHCHENO: {file_path}")
        file_size = os.path.getsize(archive_path)
        print(f"Arkhiv stvoreno: {archive_path}")
        print(f"   Rozmir: {file_size / 1024:.1f} KB")
        return archive_path

    def add_to_archive(self, archive_path, files_to_add):
        if not os.path.exists(archive_path):
            print(f"Arkhiv ne znajdeno: {archive_path}")
            return None
        with zipfile.ZipFile(archive_path, "a", zipfile.ZIP_DEFLATED) as zf:
            for file_path in files_to_add:
                if os.path.exists(file_path):
                    arcname = os.path.basename(file_path)
                    zf.write(file_path, arcname)
                    print(f"  DODANO: {arcname}")
        print("Fajly dodano do arkhivu")
        return archive_path

    def extract_archive(self, archive_path, extract_to=None):
        if extract_to is None:
            extract_to = os.path.join(self.archive_dir, "extracted")
        os.makedirs(extract_to, exist_ok=True)
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(extract_to)
        print(f"Arkhiv rozpakovano: {extract_to}")
        return extract_to

    def list_archive_contents(self, archive_path):
        with zipfile.ZipFile(archive_path, "r") as zf:
            print(f"Vmist arkhivu {os.path.basename(archive_path)}:")
            for info in zf.infolist():
                size_kb = info.file_size / 1024
                print(f"   {info.filename} ({size_kb:.1f} KB)")

    def archive_project_folder(self, project_folder, project_number):
        if not os.path.exists(project_folder):
            print(f"Papku ne znajdeno: {project_folder}")
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{project_number}_full_{timestamp}.zip"
        archive_path = os.path.join(self.archive_dir, archive_name)
        shutil.make_archive(archive_path.replace(".zip", ""), "zip", project_folder)
        print(f"Papku proektu arkhivovano: {archive_path}")
        return archive_path
