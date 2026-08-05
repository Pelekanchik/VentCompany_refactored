"""
Модуль формування специфікацій проекту
"""
from datetime import datetime
from ventilation_company.config import PROJECTS_DIR
import os


class SpecificationBuilder:
    def __init__(self, project):
        self.project = project
        self.specification = []

    def build_full_specification(self):
        spec = {
            "header": self._build_header(),
            "materials": self._build_materials_section(),
            "components": self._build_components_section(),
            "works": self._build_works_section(),
            "totals": self._calculate_totals()
        }
        self.specification = spec
        return spec

    def _build_header(self):
        return {
            "project_number": self.project.project_number,
            "project_name": self.project.name,
            "client": self.project.client,
            "address": self.project.address,
            "ventilation_type": self.project.ventilation_type,
            "air_flow": self.project.air_flow,
            "pressure": self.project.pressure,
            "date": datetime.now().strftime("%d.%m.%Y"),
            "status": self.project.status
        }

    def _build_materials_section(self):
        materials = []
        for mat in self.project._materials:
            materials.append({
                "num": len(materials) + 1,
                "name": mat["name"],
                "qty": mat["quantity"],
                "unit": mat["unit"],
                "price": mat["unit_price"],
                "total": mat["total_price"]
            })
        return materials

    def _build_components_section(self):
        components = []
        for comp in self.project._components:
            components.append({
                "num": len(components) + 1,
                "name": comp["name"],
                "qty": comp["quantity"],
                "unit": comp["unit"],
                "price": comp["unit_price"],
                "total": comp["total_price"]
            })
        return components

    def _build_works_section(self):
        works = []
        for work in self.project._works:
            works.append({
                "num": len(works) + 1,
                "name": work["name"],
                "qty": work["quantity"],
                "unit": work["unit"],
                "price": work["unit_price"],
                "total": work["total_price"]
            })
        return works

    def _calculate_totals(self):
        materials_total = sum(m["total_price"] for m in self.project._materials)
        components_total = sum(c["total_price"] for c in self.project._components)
        works_total = sum(w["total_price"] for w in self.project._works)
        return {
            "materials_total": round(materials_total, 2),
            "components_total": round(components_total, 2),
            "works_total": round(works_total, 2),
            "grand_total": round(materials_total + components_total + works_total, 2)
        }

    def print_specification(self):
        spec = self.build_full_specification()
        header = spec["header"]
        print("=" * 80)
        print("SPECYFIKACIYA PROEKTU".center(80))
        print("=" * 80)
        print(f"  Proekt: {header['project_number']} - {header['project_name']}")
        print(f"  Zamovnyk: {header['client']}")
        print(f"  Adresa: {header['address']}")
        print(f"  Typ ventyljacii: {header['ventilation_type']}")
        print(f"  Vytrata povitria: {header['air_flow']} m3/hod")
        print(f"  Data: {header['date']}")
        print("=" * 80)
        if spec["materials"]:
            print("\nMATERIALY".center(80))
            print("-" * 80)
            for item in spec["materials"]:
                print(f"  {item['num']}. {item['name']} - {item['qty']} {item['unit']} x {item['price']} = {item['total']} hrn")
        if spec["components"]:
            print("\nKOMPLEKTUUCHI".center(80))
            print("-" * 80)
            for item in spec["components"]:
                print(f"  {item['num']}. {item['name']} - {item['qty']} {item['unit']} x {item['price']} = {item['total']} hrn")
        if spec["works"]:
            print("\nROBOTY".center(80))
            print("-" * 80)
            for item in spec["works"]:
                print(f"  {item['num']}. {item['name']} - {item['qty']} {item['unit']} x {item['price']} = {item['total']} hrn")
        totals = spec["totals"]
        print("\n" + "=" * 80)
        print("PIDSUMKY".center(80))
        print("-" * 80)
        print(f"  Materialy: {totals['materials_total']:.2f} hrn")
        print(f"  Komplektuuchi: {totals['components_total']:.2f} hrn")
        print(f"  Roboty: {totals['works_total']:.2f} hrn")
        print("-" * 80)
        print(f"  VSOHO: {totals['grand_total']:.2f} hrn")
        print("=" * 80)

    def export_to_txt(self, filepath=None):
        if filepath is None:
            filepath = os.path.join(PROJECTS_DIR, f"{self.project.project_number}_spec.txt")
        spec = self.build_full_specification()
        lines = []
        header = spec["header"]
        lines.append("=" * 80)
        lines.append("SPECYFIKACIYA PROEKTU".center(80))
        lines.append("=" * 80)
        lines.append(f"Proekt: {header['project_number']} - {header['project_name']}")
        lines.append(f"Zamovnyk: {header['client']}")
        lines.append(f"Adresa: {header['address']}")
        lines.append(f"Typ: {header['ventilation_type']}")
        lines.append(f"Vytrata povitria: {header['air_flow']} m3/hod")
        lines.append(f"Data: {header['date']}")
        lines.append("=" * 80)
        for section_name, section_data in [("MATERIALY", spec["materials"]),
                                              ("KOMPLEKTUUCHI", spec["components"]),
                                              ("ROBOTY", spec["works"])]:
            if section_data:
                lines.append("")
                lines.append(section_name.center(80))
                lines.append("-" * 80)
                for item in section_data:
                    lines.append(f"{item['num']}. {item['name']} - {item['qty']} {item['unit']} x {item['price']} = {item['total']} hrn")
                lines.append("-" * 80)
        lines.append("")
        lines.append(f"VSOHO: {spec['totals']['grand_total']:.2f} hrn")
        lines.append("=" * 80)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Specyfikaciju eksportovano: {filepath}")
        return filepath
