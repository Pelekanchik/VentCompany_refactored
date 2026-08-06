#!/usr/bin/env python3
"""
freecad_exporter.py — Експорт CAD у FreeCAD
Варіант 1: Прямий імпорт (Linux / Python 3.11)
Варіант 2: CLI через freecadcmd.exe (Windows)
"""
import os
import subprocess
import sys
import tempfile

# --- FreeCAD шляхи ---
FREECAD_PATHS = [
    "/usr/lib/freecad/lib",
    "/usr/lib/freecad-daily/lib",
    "C:\\Program Files\\FreeCAD 0.21\\bin",
    "C:\\Program Files\\FreeCAD 1.0\\bin",
    "C:\\Program Files\\FreeCAD 1.1\\bin",
]

FREECAD_CMD = r"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe"

FREECAD_AVAILABLE = False
FREECAD_IMPORT = False

# Спробуємо імпортувати
for path in FREECAD_PATHS:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

try:
    import Draft  # noqa: F401
    import FreeCAD as App  # noqa: F401
    import Part  # noqa: F401

    FREECAD_AVAILABLE = True
    FREECAD_IMPORT = True
except ImportError:
    pass

# Спробуємо знайти freecadcmd (Windows CLI)
if not FREECAD_AVAILABLE and os.path.exists(FREECAD_CMD):
    FREECAD_AVAILABLE = True


class FreeCADExporter:
    """Експортує CAD-об'єкти у FreeCAD .FCStd"""

    def __init__(self):
        if not FREECAD_AVAILABLE:
            raise ImportError(
                "FreeCAD not found!\n"
                "Install: https://www.freecadweb.org/downloads.php\n"
                "Linux: sudo apt install freecad\n"
                "Windows: download installer"
            )

    def export_entities(self, entities, filepath):
        """Експорт через прямий імпорт або CLI"""
        if FREECAD_IMPORT:
            return self._export_import(entities, filepath)
        else:
            return self._export_cli(entities, filepath)

    def _export_import(self, entities, filepath):
        """Експорт через прямий імпорт модулів"""
        import Draft  # noqa: F401
        import FreeCAD as App  # noqa: F401
        import Part  # noqa: F401

        doc = App.newDocument("VentilationProject")

        for i, entity in enumerate(entities):
            type_name = type(entity).__name__
            name = f"obj_{i}"

            if type_name == "CADLine":
                line = Part.makeLine((entity.p1.x, entity.p1.y, 0), (entity.p2.x, entity.p2.y, 0))
                edge = doc.addObject("Part::Feature", name)
                edge.Shape = line

            elif type_name == "CADRectangle":
                x1, y1 = entity.p1.x, entity.p1.y
                x2, y2 = entity.p2.x, entity.p2.y
                w, h = abs(x2 - x1), abs(y2 - y1)
                box = doc.addObject("Part::Box", name)
                box.Length = max(w, h)
                box.Width = min(w, h)
                box.Height = 50
                box.Placement.Base = App.Vector(min(x1, x2), min(y1, y2), 0)

            elif type_name == "CADCircle":
                cyl = doc.addObject("Part::Cylinder", name)
                cyl.Radius = entity.radius
                cyl.Height = 100
                cyl.Placement.Base = App.Vector(entity.center.x, entity.center.y, 0)

            elif type_name == "CADArc":
                torus = doc.addObject("Part::Torus", name)
                torus.Radius1 = entity.radius * 2
                torus.Radius2 = entity.radius
                torus.Angle1 = entity.start_angle
                torus.Angle2 = entity.end_angle
                torus.Placement.Base = App.Vector(entity.center.x, entity.center.y, 0)

            elif type_name == "CADPolyline" and len(entity.points) >= 2:
                pts = [(p.x, p.y, 0) for p in entity.points]
                wire = Part.makePolygon(pts)
                poly = doc.addObject("Part::Feature", name)
                poly.Shape = wire

            elif type_name == "CADText":
                text = Draft.makeText(
                    entity.text,
                    placement=App.Placement(App.Vector(entity.x, entity.y, 0), App.Rotation()),
                )
                text.Label = name

        doc.recompute()
        doc.saveAs(filepath)
        App.closeDocument(doc.Name)
        return filepath

    def _export_cli(self, entities, filepath):
        """Експорт через freecadcmd.exe (Windows)"""

        if not os.path.exists(FREECAD_CMD):
            raise FileNotFoundError(f"freecadcmd.exe not found: {FREECAD_CMD}")

        # Генеруємо Python скрипт
        lines = [
            "import FreeCAD as App  # noqa: F401",
            "import Part  # noqa: F401",
            "import Draft  # noqa: F401",
            "",
            'doc = App.newDocument("Ventilation")',
            "",
        ]

        for i, entity in enumerate(entities):
            type_name = type(entity).__name__
            name = f"obj_{i}"

            if type_name == "CADLine":
                lines.append(
                    f"line = Part.makeLine(({entity.p1.x}, {entity.p1.y}, 0), ({entity.p2.x}, {entity.p2.y}, 0))"
                )
                lines.append(f"edge = doc.addObject('Part::Feature', '{name}')")
                lines.append("edge.Shape = line")
                lines.append("")

            elif type_name == "CADRectangle":
                x1, y1 = entity.p1.x, entity.p1.y
                x2, y2 = entity.p2.x, entity.p2.y
                w, h = abs(x2 - x1), abs(y2 - y1)
                lines.append(f"box = doc.addObject('Part::Box', '{name}')")
                lines.append(f"box.Length = {max(w,h)}")
                lines.append(f"box.Width = {min(w,h)}")
                lines.append("box.Height = 50")
                lines.append(f"box.Placement.Base = App.Vector({min(x1,x2)}, {min(y1,y2)}, 0)")
                lines.append("")

            elif type_name == "CADCircle":
                lines.append(f"cyl = doc.addObject('Part::Cylinder', '{name}')")
                lines.append(f"cyl.Radius = {entity.radius}")
                lines.append("cyl.Height = 100")
                lines.append(
                    f"cyl.Placement.Base = App.Vector({entity.center.x}, {entity.center.y}, 0)"
                )
                lines.append("")

            elif type_name == "CADArc":
                lines.append(f"torus = doc.addObject('Part::Torus', '{name}')")
                lines.append(f"torus.Radius1 = {entity.radius * 2}")
                lines.append(f"torus.Radius2 = {entity.radius}")
                lines.append(f"torus.Angle1 = {entity.start_angle}")
                lines.append(f"torus.Angle2 = {entity.end_angle}")
                lines.append(
                    f"torus.Placement.Base = App.Vector({entity.center.x}, {entity.center.y}, 0)"
                )
                lines.append("")

            elif type_name == "CADPolyline" and len(entity.points) >= 2:
                pts = ", ".join([f"({p.x}, {p.y}, 0)" for p in entity.points])
                lines.append(f"pts = [{pts}]")
                lines.append("wire = Part.makePolygon(pts)")
                lines.append(f"poly = doc.addObject('Part::Feature', '{name}')")
                lines.append("poly.Shape = wire")
                lines.append("")

            elif type_name == "CADText":
                txt = entity.text.replace("'", "\\'")
                lines.append(
                    f"text = Draft.makeText('{txt}', placement=App.Placement(App.Vector({entity.x}, {entity.y}, 0), App.Rotation()))"
                )
                lines.append(f"text.Label = '{name}'")
                lines.append("")

        lines.extend(
            [
                "doc.recompute()",
                f'doc.saveAs(r"{filepath}")',
                "App.closeDocument(doc.Name)",
            ]
        )

        # Тимчасовий скрипт
        fd, script_path = tempfile.mkstemp(suffix=".py")
        with os.fdopen(fd, "w") as f:
            f.write("\n".join(lines))

        # Запуск
        result = subprocess.run([FREECAD_CMD, script_path], capture_output=True, text=True)
        os.unlink(script_path)

        if result.returncode != 0:
            raise RuntimeError(f"FreeCAD error: {result.stderr}")

        if os.path.exists(filepath):
            return filepath
        raise RuntimeError("FreeCAD did not create file")


def check_freecad():
    """Перевірка FreeCAD"""
    print("Checking FreeCAD...")

    if FREECAD_IMPORT:
        import FreeCAD as App  # noqa: F401

        print(f"  Direct import: OK (v{App.Version()})")
        return True

    if os.path.exists(FREECAD_CMD):
        print(f"  CLI mode: OK ({FREECAD_CMD})")
        return True

    print("  Not found!")
    print("  Install from: https://www.freecadweb.org/downloads.php")
    return False


if __name__ == "__main__":
    check_freecad()
