r"""
Експортер у FreeCAD (.FCStd).
Створює 3D-моделі з CAD-сутностей (лінії, кола, прямокутники, полілінії).

Вимоги:
    - Встановлений FreeCAD (https://www.freecad.org/downloads.php)
    - FreeCAD доступний у PYTHONPATH

Windows: додайте у системну змінну PYTHONPATH:
    C:\Program Files\FreeCAD 1.0\bin
    C:\Program Files\FreeCAD 1.0\lib
"""

import math
import os
import sys

FREECAD_AVAILABLE = False
FreeCAD = None
Part = None
Draft = None

# Спробуємо знайти FreeCAD у типових місцях
_freecad_paths = [
    "C:/\\Program Files/FreeCAD 1.0/bin",
    "C:/\\Program Files/FreeCAD 0.21/bin",
    "C:/\\Program Files/FreeCAD 1.1/bin",
    "/usr/lib/freecad/lib",
    "/usr/lib/freecad-daily/lib",
    "/usr/local/lib/freecad/lib",
    "/Applications/FreeCAD.app/Contents/lib",
]

for p in _freecad_paths:
    if os.path.exists(p) and p not in sys.path:
        sys.path.append(p)

try:
    import Draft
    import FreeCAD as FC
    import Part

    FreeCAD = FC
    FREECAD_AVAILABLE = True
except ImportError:
    pass


def check_freecad():
    """Перевірити чи доступний FreeCAD."""
    return FREECAD_AVAILABLE


class FreeCADExporter:
    """Експортер CAD-сутностей у FreeCAD .FCStd файл."""

    def __init__(self):
        self.doc = None
        if not FREECAD_AVAILABLE:
            raise RuntimeError(
                "FreeCAD не знайдено. Встановіть FreeCAD та додайте його lib/ у PYTHONPATH."
            )

    def create_document(self, name="VentProject"):
        """Створити новий FreeCAD документ."""
        self.doc = FreeCAD.newDocument(name)
        return self.doc

    def _make_wire(self, points, closed=False):
        """Створити Part.Wire зі списку точок."""
        vectors = [FreeCAD.Vector(p.x, p.y, 0) for p in points]
        edges = []
        for i in range(len(vectors) - 1):
            edges.append(Part.makeLine(vectors[i], vectors[i + 1]))
        if closed and len(vectors) > 2:
            edges.append(Part.makeLine(vectors[-1], vectors[0]))
        if not edges:
            return None
        wire = Part.Wire(edges)
        return wire

    def export_line(self, line, thickness=0.7, name="Line"):
        """Експортувати лінію як тонкий профіль (для листового металу)."""
        p1 = FreeCAD.Vector(line.p1.x, line.p1.y, 0)
        p2 = FreeCAD.Vector(line.p2.x, line.p2.y, 0)
        edge = Part.makeLine(p1, p2)

        # Для вентиляції: створюємо прямокутний профіль товщиною `thickness`
        # перпендикулярно лінії
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        length = math.hypot(dx, dy)
        if length < 1e-9:
            return None

        # Нормаль (перпендикуляр)
        nx = -dy / length * (thickness / 2)
        ny = dx / length * (thickness / 2)

        # Прямокутник вздовж лінії
        pts = [
            FreeCAD.Vector(p1.x + nx, p1.y + ny, 0),
            FreeCAD.Vector(p2.x + nx, p2.y + ny, 0),
            FreeCAD.Vector(p2.x - nx, p2.y - ny, 0),
            FreeCAD.Vector(p1.x - nx, p1.y - ny, 0),
            FreeCAD.Vector(p1.x + nx, p1.y + ny, 0),
        ]
        wire = Part.makePolygon(pts)
        face = Part.Face(wire)

        obj = self.doc.addObject("Part::Feature", name)
        obj.Shape = face
        return obj

    def export_rectangle(self, rect, thickness=0.7, name="RectDuct"):
        """Експортувати прямокутник як профіль повітропроводу."""
        x1, y1 = rect.p1.x, rect.p1.y
        x2, y2 = rect.p2.x, rect.p2.y

        # Зовнішній прямокутник
        outer = [
            FreeCAD.Vector(x1, y1, 0),
            FreeCAD.Vector(x2, y1, 0),
            FreeCAD.Vector(x2, y2, 0),
            FreeCAD.Vector(x1, y2, 0),
            FreeCAD.Vector(x1, y1, 0),
        ]
        wire_outer = Part.makePolygon(outer)

        # Внутрішній (з урахуванням товщини)
        t = thickness
        inner = [
            FreeCAD.Vector(x1 + t, y1 + t, 0),
            FreeCAD.Vector(x2 - t, y1 + t, 0),
            FreeCAD.Vector(x2 - t, y2 - t, 0),
            FreeCAD.Vector(x1 + t, y2 - t, 0),
            FreeCAD.Vector(x1 + t, y1 + t, 0),
        ]
        wire_inner = Part.makePolygon(inner)

        face_outer = Part.Face(wire_outer)
        face_inner = Part.Face(wire_inner)

        # Профіль = зовнішній - внутрішній
        if face_outer.isValid() and face_inner.isValid():
            shape = face_outer.cut(face_inner)
        else:
            shape = face_outer

        obj = self.doc.addObject("Part::Feature", name)
        obj.Shape = shape
        return obj

    def export_circle(self, circle, thickness=0.7, name="RoundDuct"):
        """Експортувати коло як круглий повітропровід."""
        cx, cy = circle.center.x, circle.center.y
        r = circle.radius

        # Зовнішнє коло
        outer = Part.makeCircle(r, FreeCAD.Vector(cx, cy, 0))
        wire_outer = Part.Wire([outer])
        face_outer = Part.Face(wire_outer)

        # Внутрішнє коло (з урахуванням товщини)
        if r > thickness:
            inner = Part.makeCircle(r - thickness, FreeCAD.Vector(cx, cy, 0))
            wire_inner = Part.Wire([inner])
            face_inner = Part.Face(wire_inner)
            shape = face_outer.cut(face_inner)
        else:
            shape = face_outer

        obj = self.doc.addObject("Part::Feature", name)
        obj.Shape = shape
        return obj

    def export_polyline(self, poly, thickness=0.7, name="Polyline"):
        """Експортувати полілінію."""
        wire = self._make_wire(poly.points, poly.closed)
        if wire is None:
            return None

        if poly.closed and len(poly.points) > 2:
            face = Part.Face(wire)
            obj = self.doc.addObject("Part::Feature", name)
            obj.Shape = face
        else:
            obj = self.doc.addObject("Part::Feature", name)
            obj.Shape = wire
        return obj

    def export_arc(self, arc, thickness=0.7, name="Arc"):
        """Експортувати дугу."""
        cx, cy = arc.center.x, arc.center.y
        r = arc.radius
        sa = math.radians(arc.start_angle)
        ea = math.radians(arc.end_angle)

        arc_shape = Part.makeCircle(
            r, FreeCAD.Vector(cx, cy, 0), FreeCAD.Vector(0, 0, 1), arc.start_angle, arc.end_angle
        )
        wire = Part.Wire([arc_shape])

        obj = self.doc.addObject("Part::Feature", name)
        obj.Shape = wire
        return obj

    def export_entities(self, entities, filepath, thickness=0.7):
        """Експортувати список CAD-сутностей у .FCStd файл."""
        self.create_document()

        for i, e in enumerate(entities):
            name = f"{type(e).__name__}_{i+1}"
            try:
                from ventilation_company.cad_editor import (
                    CADArc,
                    CADCircle,
                    CADHole,
                    CADLine,
                    CADPolyline,
                    CADRectangle,
                )

                if isinstance(e, CADLine):
                    self.export_line(e, thickness, name)
                elif isinstance(e, CADRectangle):
                    self.export_rectangle(e, thickness, name)
                elif isinstance(e, CADCircle):
                    self.export_circle(e, thickness, name)
                elif isinstance(e, CADPolyline):
                    self.export_polyline(e, thickness, name)
                elif isinstance(e, CADArc):
                    self.export_arc(e, thickness, name)
                elif isinstance(e, CADHole):
                    self.export_circle(e, e.radius, name)  # Отвір як коло
                # Текст, розміри, штрихування — пропускаємо (2D-анотації)
            except Exception as ex:
                print(f"Помилка експорту {name}: {ex}")

        self.doc.recompute()
        self.doc.saveAs(filepath)
        return filepath

    def export_to_dxf(self, entities, filepath):
        """Експортувати у DXF через FreeCAD (якщо доступний ImportDXF)."""
        self.create_document()

        for i, e in enumerate(entities):
            name = f"{type(e).__name__}_{i+1}"
            try:
                from ventilation_company.cad_editor import (
                    CADArc,
                    CADCircle,
                    CADLine,
                    CADPolyline,
                    CADRectangle,
                )

                if isinstance(e, CADLine):
                    self.export_line(e, name=name)
                elif isinstance(e, CADRectangle):
                    self.export_rectangle(e, name=name)
                elif isinstance(e, CADCircle):
                    self.export_circle(e, name=name)
                elif isinstance(e, CADPolyline):
                    self.export_polyline(e, name=name)
                elif isinstance(e, CADArc):
                    self.export_arc(e, name=name)
            except Exception as ex:
                print(f"Помилка експорту {name}: {ex}")

        self.doc.recompute()

        # Спробуємо експортувати у DXF
        try:
            import Import

            Import.export(self.doc.Objects, filepath)
        except ImportError:
            # Fallback: зберегти як FCStd і повідомити
            fcstd_path = filepath.replace(".dxf", ".FCStd")
            self.doc.saveAs(fcstd_path)
            raise RuntimeError(f"DXF-експорт недоступний. Збережено як {fcstd_path}")

        return filepath

    def close(self):
        """Закрити документ."""
        if self.doc:
            FreeCAD.closeDocument(self.doc.Name)
            self.doc = None


# =========================================================
# ШВИДКІ ФУНКЦІЇ
# =========================================================


def export_to_freecad(entities, filepath, thickness=0.7):
    """Швидкий експорт списку сутностей у FreeCAD файл."""
    exporter = FreeCADExporter()
    return exporter.export_entities(entities, filepath, thickness)
