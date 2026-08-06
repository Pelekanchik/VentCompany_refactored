#!/usr/bin/env python3
"""
CAD Редактор 2.0 — Об'єднана версія
"""
import json
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# --- FreeCAD інтеграція ---
try:
    from .freecad_exporter import FREECAD_AVAILABLE, FreeCADExporter, check_freecad
except ImportError:
    try:
        from freecad_exporter import FREECAD_AVAILABLE, FreeCADExporter, check_freecad
    except ImportError:
        FREECAD_AVAILABLE = False
        FreeCADExporter = None

        def check_freecad():
            return False


# ===================== geometry =====================


def point_in_polygon(x, y, poly):
    """Ray-casting algorithm для визначення чи точка всередині полігона"""
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(1, n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y) and y <= max(p1y, p2y) and x <= max(p1x, p2x):
            if p1y != p2y:
                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
            if p1x == p2x or x <= xinters:
                inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def line_intersection(p1, p2, p3, p4):
    """Повертає точку перетину двох відрізків або None"""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-9:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    if 0 <= t <= 1 and 0 <= u <= 1:
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    return None


def offset_line(x1, y1, x2, y2, distance):
    """Повертає паралельну лінію на відстані distance (з правого боку)"""
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return None
    ux, uy = dx / length, dy / length
    nx, ny = uy, -ux
    return (x1 + nx * distance, y1 + ny * distance, x2 + nx * distance, y2 + ny * distance)


def distance_point_to_line(px, py, x1, y1, x2, y2):
    """Відстань від точки до відрізка"""
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def rotate_point(x, y, cx, cy, angle_deg):
    """Обертання точки навколо центру"""
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    dx = x - cx
    dy = y - cy
    return (cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a)


# ===================== entities =====================


class CADPoint:
    """Точка на кресленні"""

    __slots__ = ("x", "y", "snap")

    def __init__(self, x, y, snap=True):
        self.x = float(x)
        self.y = float(y)
        self.snap = snap

    def __repr__(self):
        return f"P({self.x:.2f},{self.y:.2f})"

    def __eq__(self, other):
        return abs(self.x - other.x) < 0.01 and abs(self.y - other.y) < 0.01

    def copy(self):
        return CADPoint(self.x, self.y, self.snap)

    def to_tuple(self):
        return (self.x, self.y)


class CADEntity:
    """Базовий клас графічного примітива"""

    _id_counter = 0

    def __init__(self, layer="0", color="#2c3e50", line_width=1):
        CADEntity._id_counter += 1
        self.id = CADEntity._id_counter
        self.layer = layer
        self.color = color
        self.line_width = line_width
        self.selected = False
        self._cached_bbox = None

    def bbox(self):
        raise NotImplementedError

    def hit_test(self, x, y, tol=5):
        raise NotImplementedError

    def get_snap_points(self):
        return []

    def copy_entity(self):
        raise NotImplementedError

    def move(self, dx, dy):
        raise NotImplementedError

    def rotate(self, cx, cy, angle_deg):
        raise NotImplementedError

    def mirror(self, x1, y1, x2, y2):
        raise NotImplementedError

    def area(self):
        return 0.0

    def perimeter(self):
        return 0.0

    def invalidate_bbox(self):
        self._cached_bbox = None

    def get_cached_bbox(self):
        if self._cached_bbox is None:
            self._cached_bbox = self.bbox()
        return self._cached_bbox


class CADLine(CADEntity):
    def __init__(self, p1, p2, **kwargs):
        super().__init__(**kwargs)
        self.p1 = p1
        self.p2 = p2

    def bbox(self):
        return (
            min(self.p1.x, self.p2.x),
            min(self.p1.y, self.p2.y),
            max(self.p1.x, self.p2.x),
            max(self.p1.y, self.p2.y),
        )

    def length(self):
        return math.hypot(self.p2.x - self.p1.x, self.p2.y - self.p1.y)

    def midpoint(self):
        return ((self.p1.x + self.p2.x) / 2, (self.p1.y + self.p2.y) / 2)

    def hit_test(self, x, y, tol=5):
        return distance_point_to_line(x, y, self.p1.x, self.p1.y, self.p2.x, self.p2.y) <= tol

    def get_snap_points(self):
        mx, my = self.midpoint()
        return [
            (self.p1.x, self.p1.y, "endpoint"),
            (self.p2.x, self.p2.y, "endpoint"),
            (mx, my, "midpoint"),
        ]

    def copy_entity(self):
        return CADLine(
            self.p1.copy(),
            self.p2.copy(),
            layer=self.layer,
            color=self.color,
            line_width=self.line_width,
        )

    def move(self, dx, dy):
        self.p1.x += dx
        self.p1.y += dy
        self.p2.x += dx
        self.p2.y += dy
        self.invalidate_bbox()

    def rotate(self, cx, cy, angle_deg):
        self.p1.x, self.p1.y = rotate_point(self.p1.x, self.p1.y, cx, cy, angle_deg)
        self.p2.x, self.p2.y = rotate_point(self.p2.x, self.p2.y, cx, cy, angle_deg)
        self.invalidate_bbox()

    def mirror(self, x1, y1, x2, y2):
        def _mirror(px, py):
            dx_line = x2 - x1
            dy_line = y2 - y1
            len2 = dx_line**2 + dy_line**2
            if len2 == 0:
                return (px, py)
            t = ((px - x1) * dx_line + (py - y1) * dy_line) / len2
            proj_x = x1 + t * dx_line
            proj_y = y1 + t * dy_line
            return (2 * proj_x - px, 2 * proj_y - py)

        self.p1.x, self.p1.y = _mirror(self.p1.x, self.p1.y)
        self.p2.x, self.p2.y = _mirror(self.p2.x, self.p2.y)
        self.invalidate_bbox()

    def perimeter(self):
        return self.length()


class CADRectangle(CADEntity):
    def __init__(self, p1, p2, **kwargs):
        super().__init__(**kwargs)
        self.p1 = p1
        self.p2 = p2

    def bbox(self):
        return (
            min(self.p1.x, self.p2.x),
            min(self.p1.y, self.p2.y),
            max(self.p1.x, self.p2.x),
            max(self.p1.y, self.p2.y),
        )

    def width(self):
        return abs(self.p2.x - self.p1.x)

    def height(self):
        return abs(self.p2.y - self.p1.y)

    def hit_test(self, x, y, tol=5):
        bx1, by1, bx2, by2 = self.bbox()
        return (
            bx1 - tol <= x <= bx2 + tol
            and by1 - tol <= y <= by2 + tol
            and (x <= bx1 + tol or x >= bx2 - tol or y <= by1 + tol or y >= by2 - tol)
        )

    def get_snap_points(self):
        x1, y1 = self.p1.x, self.p1.y
        x2, y2 = self.p2.x, self.p2.y
        return [
            (x1, y1, "endpoint"),
            (x2, y1, "endpoint"),
            (x1, y2, "endpoint"),
            (x2, y2, "endpoint"),
            ((x1 + x2) / 2, (y1 + y2) / 2, "midpoint"),
        ]

    def copy_entity(self):
        return CADRectangle(
            self.p1.copy(),
            self.p2.copy(),
            layer=self.layer,
            color=self.color,
            line_width=self.line_width,
        )

    def move(self, dx, dy):
        self.p1.x += dx
        self.p1.y += dy
        self.p2.x += dx
        self.p2.y += dy
        self.invalidate_bbox()

    def rotate(self, cx, cy, angle_deg):
        self.p1.x, self.p1.y = rotate_point(self.p1.x, self.p1.y, cx, cy, angle_deg)
        self.p2.x, self.p2.y = rotate_point(self.p2.x, self.p2.y, cx, cy, angle_deg)
        self.invalidate_bbox()

    def mirror(self, x1, y1, x2, y2):
        def _mirror(px, py):
            dx_line = x2 - x1
            dy_line = y2 - y1
            len2 = dx_line**2 + dy_line**2
            if len2 == 0:
                return (px, py)
            t = ((px - x1) * dx_line + (py - y1) * dy_line) / len2
            proj_x = x1 + t * dx_line
            proj_y = y1 + t * dy_line
            return (2 * proj_x - px, 2 * proj_y - py)

        self.p1.x, self.p1.y = _mirror(self.p1.x, self.p1.y)
        self.p2.x, self.p2.y = _mirror(self.p2.x, self.p2.y)
        self.invalidate_bbox()

    def area(self):
        return self.width() * self.height()

    def perimeter(self):
        return 2 * (self.width() + self.height())


class CADCircle(CADEntity):
    def __init__(self, center, radius, **kwargs):
        super().__init__(**kwargs)
        self.center = center
        self.radius = float(radius)

    def bbox(self):
        return (
            self.center.x - self.radius,
            self.center.y - self.radius,
            self.center.x + self.radius,
            self.center.y + self.radius,
        )

    def hit_test(self, x, y, tol=5):
        d = math.hypot(x - self.center.x, y - self.center.y)
        return abs(d - self.radius) <= tol

    def get_snap_points(self):
        cx, cy = self.center.x, self.center.y
        r = self.radius
        return [
            (cx, cy, "center"),
            (cx + r, cy, "quadrant"),
            (cx - r, cy, "quadrant"),
            (cx, cy + r, "quadrant"),
            (cx, cy - r, "quadrant"),
        ]

    def copy_entity(self):
        return CADCircle(
            self.center.copy(),
            self.radius,
            layer=self.layer,
            color=self.color,
            line_width=self.line_width,
        )

    def move(self, dx, dy):
        self.center.x += dx
        self.center.y += dy
        self.invalidate_bbox()

    def rotate(self, cx, cy, angle_deg):
        self.center.x, self.center.y = rotate_point(self.center.x, self.center.y, cx, cy, angle_deg)
        self.invalidate_bbox()

    def mirror(self, x1, y1, x2, y2):
        def _mirror(px, py):
            dx_line = x2 - x1
            dy_line = y2 - y1
            len2 = dx_line**2 + dy_line**2
            if len2 == 0:
                return (px, py)
            t = ((px - x1) * dx_line + (py - y1) * dy_line) / len2
            proj_x = x1 + t * dx_line
            proj_y = y1 + t * dy_line
            return (2 * proj_x - px, 2 * proj_y - py)

        self.center.x, self.center.y = _mirror(self.center.x, self.center.y)
        self.invalidate_bbox()

    def area(self):
        return math.pi * self.radius**2

    def perimeter(self):
        return 2 * math.pi * self.radius


class CADArc(CADEntity):
    def __init__(self, center, radius, start_angle, end_angle, **kwargs):
        super().__init__(**kwargs)
        self.center = center
        self.radius = float(radius)
        self.start_angle = float(start_angle)
        self.end_angle = float(end_angle)

    def bbox(self):
        pts = []
        for ang in [
            self.start_angle,
            self.end_angle,
            (self.start_angle + self.end_angle) / 2,
            self.start_angle + 90,
            self.end_angle - 90,
        ]:
            rad = math.radians(ang)
            pts.append(
                (
                    self.center.x + self.radius * math.cos(rad),
                    self.center.y + self.radius * math.sin(rad),
                )
            )
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    def hit_test(self, x, y, tol=5):
        d = math.hypot(x - self.center.x, y - self.center.y)
        if abs(d - self.radius) > tol:
            return False
        angle = math.degrees(math.atan2(y - self.center.y, x - self.center.x))
        while angle < 0:
            angle += 360
        sa, ea = self.start_angle % 360, self.end_angle % 360
        if sa <= ea:
            return sa <= angle <= ea
        return angle >= sa or angle <= ea

    def get_snap_points(self):
        cx, cy = self.center.x, self.center.y
        r = self.radius
        pts = [(cx, cy, "center")]
        for ang in [self.start_angle, self.end_angle, (self.start_angle + self.end_angle) / 2]:
            rad = math.radians(ang)
            pts.append((cx + r * math.cos(rad), cy + r * math.sin(rad), "endpoint"))
        return pts

    def copy_entity(self):
        return CADArc(
            self.center.copy(),
            self.radius,
            self.start_angle,
            self.end_angle,
            layer=self.layer,
            color=self.color,
            line_width=self.line_width,
        )

    def move(self, dx, dy):
        self.center.x += dx
        self.center.y += dy
        self.invalidate_bbox()

    def rotate(self, cx, cy, angle_deg):
        self.center.x, self.center.y = rotate_point(self.center.x, self.center.y, cx, cy, angle_deg)
        self.start_angle = (self.start_angle + angle_deg) % 360
        self.end_angle = (self.end_angle + angle_deg) % 360
        self.invalidate_bbox()

    def mirror(self, x1, y1, x2, y2):
        def _mirror(px, py):
            dx_line = x2 - x1
            dy_line = y2 - y1
            len2 = dx_line**2 + dy_line**2
            if len2 == 0:
                return (px, py)
            t = ((px - x1) * dx_line + (py - y1) * dy_line) / len2
            proj_x = x1 + t * dx_line
            proj_y = y1 + t * dy_line
            return (2 * proj_x - px, 2 * proj_y - py)

        self.center.x, self.center.y = _mirror(self.center.x, self.center.y)
        line_angle = math.degrees(math.atan2(y2 - y1, x2 - x1))

        def mirror_angle(a):
            diff = a - line_angle
            return (line_angle - diff) % 360

        self.start_angle = mirror_angle(self.start_angle)
        self.end_angle = mirror_angle(self.end_angle)
        if self.start_angle > self.end_angle:
            self.start_angle, self.end_angle = self.end_angle, self.start_angle
        self.invalidate_bbox()

    def arc_length(self):
        sa, ea = self.start_angle, self.end_angle
        if ea < sa:
            ea += 360
        return math.radians(ea - sa) * self.radius

    def perimeter(self):
        return self.arc_length()


class CADDimension(CADEntity):
    def __init__(self, p1, p2, offset=15, text=None, **kwargs):
        super().__init__(layer="DIM", color="#c0392b", line_width=1, **kwargs)
        self.p1 = p1
        self.p2 = p2
        self.offset = offset
        self.text = text

    def value(self):
        return math.hypot(self.p2.x - self.p1.x, self.p2.y - self.p1.y)

    def bbox(self):
        return (
            min(self.p1.x, self.p2.x),
            min(self.p1.y, self.p2.y),
            max(self.p1.x, self.p2.x),
            max(self.p1.y, self.p2.y),
        )

    def hit_test(self, x, y, tol=8):
        bx1, by1, bx2, by2 = self.bbox()
        return bx1 - tol <= x <= bx2 + tol and by1 - tol <= y <= by2 + tol

    def get_snap_points(self):
        return [
            (self.p1.x, self.p1.y, "endpoint"),
            (self.p2.x, self.p2.y, "endpoint"),
        ]

    def copy_entity(self):
        return CADDimension(
            self.p1.copy(),
            self.p2.copy(),
            self.offset,
            self.text,
            layer=self.layer,
            color=self.color,
            line_width=self.line_width,
        )

    def move(self, dx, dy):
        self.p1.x += dx
        self.p1.y += dy
        self.p2.x += dx
        self.p2.y += dy
        self.invalidate_bbox()

    def rotate(self, cx, cy, angle_deg):
        self.p1.x, self.p1.y = rotate_point(self.p1.x, self.p1.y, cx, cy, angle_deg)
        self.p2.x, self.p2.y = rotate_point(self.p2.x, self.p2.y, cx, cy, angle_deg)
        self.invalidate_bbox()

    def mirror(self, x1, y1, x2, y2):
        def _mirror(px, py):
            dx_line = x2 - x1
            dy_line = y2 - y1
            len2 = dx_line**2 + dy_line**2
            if len2 == 0:
                return (px, py)
            t = ((px - x1) * dx_line + (py - y1) * dy_line) / len2
            proj_x = x1 + t * dx_line
            proj_y = y1 + t * dy_line
            return (2 * proj_x - px, 2 * proj_y - py)

        self.p1.x, self.p1.y = _mirror(self.p1.x, self.p1.y)
        self.p2.x, self.p2.y = _mirror(self.p2.x, self.p2.y)
        self.invalidate_bbox()


class CADPolyline(CADEntity):
    """Полілінія — послідовність точок. Критично для профілів вентиляції."""

    def __init__(self, points, closed=False, **kwargs):
        super().__init__(**kwargs)
        self.points = list(points)
        self.closed = closed

    def bbox(self):
        if not self.points:
            return (0, 0, 0, 0)
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))

    def hit_test(self, x, y, tol=5):
        pts = self.points
        n = len(pts)
        for i in range(n - 1):
            if distance_point_to_line(x, y, pts[i].x, pts[i].y, pts[i + 1].x, pts[i + 1].y) <= tol:
                return True
        if (
            self.closed
            and n > 2
            and distance_point_to_line(x, y, pts[-1].x, pts[-1].y, pts[0].x, pts[0].y) <= tol
        ):
            return True
        if self.closed and n > 2:
            poly = [(p.x, p.y) for p in self.points]
            if point_in_polygon(x, y, poly):
                return True
        return False

    def get_snap_points(self):
        pts = []
        for p in self.points:
            pts.append((p.x, p.y, "endpoint"))
        for i in range(len(self.points) - 1):
            mx = (self.points[i].x + self.points[i + 1].x) / 2
            my = (self.points[i].y + self.points[i + 1].y) / 2
            pts.append((mx, my, "midpoint"))
        if self.closed and len(self.points) > 2:
            mx = (self.points[-1].x + self.points[0].x) / 2
            my = (self.points[-1].y + self.points[0].y) / 2
            pts.append((mx, my, "midpoint"))
        return pts

    def copy_entity(self):
        return CADPolyline(
            [p.copy() for p in self.points],
            self.closed,
            layer=self.layer,
            color=self.color,
            line_width=self.line_width,
        )

    def move(self, dx, dy):
        for p in self.points:
            p.x += dx
            p.y += dy
        self.invalidate_bbox()

    def rotate(self, cx, cy, angle_deg):
        for p in self.points:
            p.x, p.y = rotate_point(p.x, p.y, cx, cy, angle_deg)
        self.invalidate_bbox()

    def mirror(self, x1, y1, x2, y2):
        def _mirror(px, py):
            dx_line = x2 - x1
            dy_line = y2 - y1
            len2 = dx_line**2 + dy_line**2
            if len2 == 0:
                return (px, py)
            t = ((px - x1) * dx_line + (py - y1) * dy_line) / len2
            proj_x = x1 + t * dx_line
            proj_y = y1 + t * dy_line
            return (2 * proj_x - px, 2 * proj_y - py)

        for p in self.points:
            p.x, p.y = _mirror(p.x, p.y)
        self.invalidate_bbox()

    def perimeter(self):
        per = 0
        for i in range(len(self.points) - 1):
            per += math.hypot(
                self.points[i + 1].x - self.points[i].x, self.points[i + 1].y - self.points[i].y
            )
        if self.closed and len(self.points) > 2:
            per += math.hypot(
                self.points[0].x - self.points[-1].x, self.points[0].y - self.points[-1].y
            )
        return per

    def area(self):
        if not self.closed or len(self.points) < 3:
            return 0.0
        area = 0
        n = len(self.points)
        for i in range(n):
            j = (i + 1) % n
            area += self.points[i].x * self.points[j].y
            area -= self.points[j].x * self.points[i].y
        return abs(area) / 2

    def offset(self, distance):
        if len(self.points) < 2:
            return None
        new_pts = []
        n = len(self.points)
        for i in range(n if self.closed else n - 1):
            p0 = self.points[i]
            p1 = self.points[(i + 1) % n] if self.closed else self.points[i + 1]
            dx = p1.x - p0.x
            dy = p1.y - p0.y
            length = math.hypot(dx, dy)
            if length < 1e-9:
                continue
            ux, uy = dx / length, dy / length
            nx, ny = uy, -ux
            new_pts.append(CADPoint(p0.x + nx * distance, p0.y + ny * distance))
        return CADPolyline(
            new_pts, self.closed, layer=self.layer, color=self.color, line_width=self.line_width
        )


class CADText(CADEntity):
    """Текстова мітка — маркування деталей вентиляції"""

    def __init__(self, x, y, text, height=10, angle=0, align="left", **kwargs):
        super().__init__(**kwargs)
        self.x = x
        self.y = y
        self.text = text
        self.height = height
        self.angle = angle
        self.align = align

    def bbox(self):
        approx_width = len(self.text) * self.height * 0.6
        if self.align == "center":
            return (
                self.x - approx_width / 2,
                self.y - self.height,
                self.x + approx_width / 2,
                self.y + self.height / 4,
            )
        elif self.align == "right":
            return (self.x - approx_width, self.y - self.height, self.x, self.y + self.height / 4)
        else:
            return (self.x, self.y - self.height, self.x + approx_width, self.y + self.height / 4)

    def hit_test(self, x, y, tol=8):
        bx1, by1, bx2, by2 = self.bbox()
        return bx1 - tol <= x <= bx2 + tol and by1 - tol <= y <= by2 + tol

    def get_snap_points(self):
        return [(self.x, self.y, "insert")]

    def copy_entity(self):
        return CADText(
            self.x,
            self.y,
            self.text,
            self.height,
            self.angle,
            self.align,
            layer=self.layer,
            color=self.color,
            line_width=self.line_width,
        )

    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        self.invalidate_bbox()

    def rotate(self, cx, cy, angle_deg):
        self.x, self.y = rotate_point(self.x, self.y, cx, cy, angle_deg)
        self.angle = (self.angle + angle_deg) % 360
        self.invalidate_bbox()

    def mirror(self, x1, y1, x2, y2):
        def _mirror(px, py):
            dx_line = x2 - x1
            dy_line = y2 - y1
            len2 = dx_line**2 + dy_line**2
            if len2 == 0:
                return (px, py)
            t = ((px - x1) * dx_line + (py - y1) * dy_line) / len2
            proj_x = x1 + t * dx_line
            proj_y = y1 + t * dy_line
            return (2 * proj_x - px, 2 * proj_y - py)

        self.x, self.y = _mirror(self.x, self.y)
        line_angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        diff = self.angle - line_angle
        self.angle = (line_angle - diff) % 360
        self.invalidate_bbox()


class CADHatch(CADEntity):
    """Лінійне штрихування (наприклад, для позначення ізоляції)"""

    def __init__(self, boundary_points, angle=45, spacing=5, **kwargs):
        super().__init__(layer="HATCH", color="#95a5a6", line_width=1, **kwargs)
        self.boundary = list(boundary_points)
        self.hatch_angle = angle
        self.spacing = spacing

    def bbox(self):
        if not self.boundary:
            return (0, 0, 0, 0)
        xs = [p.x for p in self.boundary]
        ys = [p.y for p in self.boundary]
        return (min(xs), min(ys), max(xs), max(ys))

    def hit_test(self, x, y, tol=5):
        if len(self.boundary) < 3:
            return False
        poly = [(p.x, p.y) for p in self.boundary]
        return point_in_polygon(x, y, poly)

    def get_snap_points(self):
        if not self.boundary:
            return []
        xs = [p.x for p in self.boundary]
        ys = [p.y for p in self.boundary]
        return [((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, "midpoint")]

    def copy_entity(self):
        return CADHatch(
            [p.copy() for p in self.boundary],
            self.hatch_angle,
            self.spacing,
            layer=self.layer,
            color=self.color,
            line_width=self.line_width,
        )

    def move(self, dx, dy):
        for p in self.boundary:
            p.x += dx
            p.y += dy
        self.invalidate_bbox()

    def rotate(self, cx, cy, angle_deg):
        for p in self.boundary:
            p.x, p.y = rotate_point(p.x, p.y, cx, cy, angle_deg)
        self.hatch_angle = (self.hatch_angle + angle_deg) % 360
        self.invalidate_bbox()

    def mirror(self, x1, y1, x2, y2):
        def _mirror(px, py):
            dx_line = x2 - x1
            dy_line = y2 - y1
            len2 = dx_line**2 + dy_line**2
            if len2 == 0:
                return (px, py)
            t = ((px - x1) * dx_line + (py - y1) * dy_line) / len2
            proj_x = x1 + t * dx_line
            proj_y = y1 + t * dy_line
            return (2 * proj_x - px, 2 * proj_y - py)

        for p in self.boundary:
            p.x, p.y = _mirror(p.x, p.y)
        line_angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        diff = self.hatch_angle - line_angle
        self.hatch_angle = (line_angle - diff) % 360
        self.invalidate_bbox()


class CADHole(CADEntity):
    """Отвір — вентиляційний отвір (коло з хрестиком центрування)"""

    def __init__(self, center, radius, label="", **kwargs):
        super().__init__(layer="HOLES", color="#e67e22", line_width=1, **kwargs)
        self.center = center
        self.radius = float(radius)
        self.label = label

    def bbox(self):
        return (
            self.center.x - self.radius,
            self.center.y - self.radius,
            self.center.x + self.radius,
            self.center.y + self.radius,
        )

    def hit_test(self, x, y, tol=5):
        d = math.hypot(x - self.center.x, y - self.center.y)
        return d <= self.radius + tol

    def get_snap_points(self):
        cx, cy = self.center.x, self.center.y
        r = self.radius
        return [
            (cx, cy, "center"),
            (cx + r, cy, "quadrant"),
            (cx - r, cy, "quadrant"),
            (cx, cy + r, "quadrant"),
            (cx, cy - r, "quadrant"),
        ]

    def copy_entity(self):
        return CADHole(
            self.center.copy(),
            self.radius,
            self.label,
            layer=self.layer,
            color=self.color,
            line_width=self.line_width,
        )

    def move(self, dx, dy):
        self.center.x += dx
        self.center.y += dy
        self.invalidate_bbox()

    def rotate(self, cx, cy, angle_deg):
        self.center.x, self.center.y = rotate_point(self.center.x, self.center.y, cx, cy, angle_deg)
        self.invalidate_bbox()

    def mirror(self, x1, y1, x2, y2):
        def _mirror(px, py):
            dx_line = x2 - x1
            dy_line = y2 - y1
            len2 = dx_line**2 + dy_line**2
            if len2 == 0:
                return (px, py)
            t = ((px - x1) * dx_line + (py - y1) * dy_line) / len2
            proj_x = x1 + t * dx_line
            proj_y = y1 + t * dy_line
            return (2 * proj_x - px, 2 * proj_y - py)

        self.center.x, self.center.y = _mirror(self.center.x, self.center.y)
        self.invalidate_bbox()

    def area(self):
        return math.pi * self.radius**2

    def perimeter(self):
        return 2 * math.pi * self.radius


# ===================== commands =====================
class Command:
    """Базовий клас команди"""

    def execute(self, editor):
        raise NotImplementedError

    def undo(self, editor):
        raise NotImplementedError

    def __str__(self):
        return self.__class__.__name__


class AddEntityCmd(Command):
    def __init__(self, entity):
        self.entity = entity

    def execute(self, editor):
        editor.entities.append(self.entity)

    def undo(self, editor):
        if self.entity in editor.entities:
            editor.entities.remove(self.entity)

    def __str__(self):
        return f"Додати {type(self.entity).__name__}"


class DeleteEntityCmd(Command):
    def __init__(self, entities):
        self.entities = list(entities)
        self.indices = []

    def execute(self, editor):
        self.indices = []
        for e in self.entities:
            if e in editor.entities:
                self.indices.append(editor.entities.index(e))
                editor.entities.remove(e)

    def undo(self, editor):
        for idx, e in sorted(zip(self.indices, self.entities, strict=False), key=lambda x: x[0]):
            editor.entities.insert(idx, e)

    def __str__(self):
        return f"Видалити {len(self.entities)} об'єктів"


class MoveEntityCmd(Command):
    def __init__(self, entities, dx, dy):
        self.entities = list(entities)
        self.dx = dx
        self.dy = dy

    def execute(self, editor):
        for e in self.entities:
            e.move(self.dx, self.dy)

    def undo(self, editor):
        for e in self.entities:
            e.move(-self.dx, -self.dy)

    def __str__(self):
        return f"Зрушити на ({self.dx:.1f}, {self.dy:.1f})"


class RotateEntityCmd(Command):
    def __init__(self, entities, cx, cy, angle):
        self.entities = list(entities)
        self.cx = cx
        self.cy = cy
        self.angle = angle

    def execute(self, editor):
        for e in self.entities:
            e.rotate(self.cx, self.cy, self.angle)

    def undo(self, editor):
        for e in self.entities:
            e.rotate(self.cx, self.cy, -self.angle)

    def __str__(self):
        return f"Обертання на {self.angle:.1f}°"


class MirrorEntityCmd(Command):
    def __init__(self, entities, x1, y1, x2, y2):
        self.entities = list(entities)
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2

    def execute(self, editor):
        for e in self.entities:
            e.mirror(self.x1, self.y1, self.x2, self.y2)

    def undo(self, editor):
        for e in self.entities:
            e.mirror(self.x1, self.y1, self.x2, self.y2)

    def __str__(self):
        return "Дзеркальне відображення"


class ClearCmd(Command):
    def __init__(self):
        self.saved_entities = []

    def execute(self, editor):
        self.saved_entities = list(editor.entities)
        editor.entities.clear()

    def undo(self, editor):
        editor.entities = list(self.saved_entities)

    def __str__(self):
        return "Очистити креслення"


# ===================== core =====================


class CADEditor:
    """Ядро CAD-редактора з Undo/Redo"""

    def __init__(self):
        self.entities = []
        self.layers = {
            "0": {"visible": True, "color": "#2c3e50", "name": "Основний"},
            "CENTER": {"visible": True, "color": "#3498db", "name": "Осі"},
            "DIM": {"visible": True, "color": "#c0392b", "name": "Виміри"},
            "HATCH": {"visible": True, "color": "#95a5a6", "name": "Штрихування"},
            "HOLES": {"visible": True, "color": "#e67e22", "name": "Отвори"},
            "TEXT": {"visible": True, "color": "#8e44ad", "name": "Текст"},
        }
        self.grid_size = 10
        self.snap_size = 10
        self.unit = "мм"
        self.scale = 1.0
        self.origin_x = 0
        self.origin_y = 0
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo = 50

    def execute_command(self, cmd):
        cmd.execute(self)
        self.undo_stack.append(cmd)
        self.redo_stack.clear()
        if len(self.undo_stack) > self.max_undo:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            return False
        cmd = self.undo_stack.pop()
        cmd.undo(self)
        self.redo_stack.append(cmd)
        return True

    def redo(self):
        if not self.redo_stack:
            return False
        cmd = self.redo_stack.pop()
        cmd.execute(self)
        self.undo_stack.append(cmd)
        return True

    def can_undo(self):
        return len(self.undo_stack) > 0

    def can_redo(self):
        return len(self.redo_stack) > 0

    def add_entity(self, entity):
        self.execute_command(AddEntityCmd(entity))
        return entity

    def delete_entity(self, entity):
        if entity in self.entities:
            self.execute_command(DeleteEntityCmd([entity]))

    def delete_selected(self):
        sel = self.get_selected()
        if sel:
            self.execute_command(DeleteEntityCmd(sel))
            self.deselect_all()

    def clear(self):
        if self.entities:
            self.execute_command(ClearCmd())
        CADEntity._id_counter = 0

    def get_visible_entities(self):
        return [e for e in self.entities if self.layers.get(e.layer, {}).get("visible", True)]

    def snap_point(self, x, y, snap_modes, entities, canvas_w, canvas_h):
        best = (x, y)
        best_type = "free"
        best_dist = float("inf")
        tol = 15 / self.scale

        if snap_modes.get("grid", False):
            gx = round(x / self.snap_size) * self.snap_size
            gy = round(y / self.snap_size) * self.snap_size
            d = math.hypot(x - gx, y - gy)
            if d < best_dist:
                best_dist = d
                best = (gx, gy)
                best_type = "grid"

        for e in reversed(entities):
            for sx, sy, stype in e.get_snap_points():
                if not snap_modes.get(stype, False) and stype != "endpoint":
                    continue
                if stype == "endpoint" and not snap_modes.get("endpoint", False):
                    continue
                d = math.hypot(x - sx, y - sy)
                if d < tol and d < best_dist:
                    best_dist = d
                    best = (sx, sy)
                    best_type = stype

        return CADPoint(best[0], best[1], snap=True), best_type

    def apply_ortho(self, base_x, base_y, cur_x, cur_y):
        dx = abs(cur_x - base_x)
        dy = abs(cur_y - base_y)
        if dx > dy:
            return CADPoint(cur_x, base_y, snap=True)
        else:
            return CADPoint(base_x, cur_y, snap=True)

    def world_to_screen(self, x, y, canvas_w, canvas_h):
        sx = (x - self.origin_x) * self.scale + canvas_w / 2
        sy = canvas_h / 2 - (y - self.origin_y) * self.scale
        return sx, sy

    def screen_to_world(self, sx, sy, canvas_w, canvas_h):
        x = (sx - canvas_w / 2) / self.scale + self.origin_x
        y = self.origin_y - (sy - canvas_h / 2) / self.scale
        return x, y

    def select_at(self, x, y, tol=5, add=False):
        for e in reversed(self.get_visible_entities()):
            if e.hit_test(x, y, tol / self.scale):
                if not add:
                    self.deselect_all()
                e.selected = not e.selected if add else True
                return e
        if not add:
            self.deselect_all()
        return None

    def select_in_rect(self, x1, y1, x2, y2, add=False):
        if not add:
            self.deselect_all()
        bx1, bx2 = min(x1, x2), max(x1, x2)
        by1, by2 = min(y1, y2), max(y1, y2)
        for e in self.get_visible_entities():
            ex1, ey1, ex2, ey2 = e.get_cached_bbox()
            if ex1 >= bx1 and ex2 <= bx2 and ey1 >= by1 and ey2 <= by2:
                e.selected = True

    def select_all(self):
        for e in self.entities:
            e.selected = True

    def deselect_all(self):
        for e in self.entities:
            e.selected = False

    def get_selected(self):
        return [e for e in self.entities if e.selected]

    def move_selected(self, dx, dy):
        sel = self.get_selected()
        if sel:
            self.execute_command(MoveEntityCmd(sel, dx, dy))

    def rotate_selected(self, cx, cy, angle):
        sel = self.get_selected()
        if sel:
            self.execute_command(RotateEntityCmd(sel, cx, cy, angle))

    def mirror_selected(self, x1, y1, x2, y2):
        sel = self.get_selected()
        if sel:
            self.execute_command(MirrorEntityCmd(sel, x1, y1, x2, y2))

    def copy_selected(self):
        copies = []
        for e in self.get_selected():
            c = e.copy_entity()
            c.selected = False
            copies.append(c)
        return copies

    def get_total_area(self):
        total = 0
        for e in self.entities:
            if hasattr(e, "area"):
                total += e.area()
        return total

    def get_total_perimeter(self):
        total = 0
        for e in self.entities:
            if hasattr(e, "perimeter"):
                total += e.perimeter()
        return total

    def export_svg(self, filepath, width=800, height=600):
        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff"/>',
        ]
        for e in self.get_visible_entities():
            if isinstance(e, CADLine):
                sx1, sy1 = self.world_to_screen(e.p1.x, e.p1.y, width, height)
                sx2, sy2 = self.world_to_screen(e.p2.x, e.p2.y, width, height)
                lines.append(
                    f'  <line x1="{sx1:.1f}" y1="{sy1:.1f}" x2="{sx2:.1f}" y2="{sy2:.1f}" '
                    f'stroke="{e.color}" stroke-width="{e.line_width}"/>'
                )
            elif isinstance(e, CADRectangle):
                sx1, sy1 = self.world_to_screen(e.p1.x, e.p1.y, width, height)
                sx2, sy2 = self.world_to_screen(e.p2.x, e.p2.y, width, height)
                rx, ry = min(sx1, sx2), min(sy1, sy2)
                rw, rh = abs(sx2 - sx1), abs(sy2 - sy1)
                lines.append(
                    f'  <rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" '
                    f'fill="none" stroke="{e.color}" stroke-width="{e.line_width}"/>'
                )
            elif isinstance(e, CADCircle):
                sx, sy = self.world_to_screen(e.center.x, e.center.y, width, height)
                sr = e.radius * self.scale
                lines.append(
                    f'  <circle cx="{sx:.1f}" cy="{sy:.1f}" r="{sr:.1f}" '
                    f'fill="none" stroke="{e.color}" stroke-width="{e.line_width}"/>'
                )
            elif isinstance(e, CADDimension):
                sx1, sy1 = self.world_to_screen(e.p1.x, e.p1.y, width, height)
                sx2, sy2 = self.world_to_screen(e.p2.x, e.p2.y, width, height)
                val = e.value()
                mx, my = (sx1 + sx2) / 2, (sy1 + sy2) / 2 - 5
                lines.append(
                    f'  <line x1="{sx1:.1f}" y1="{sy1:.1f}" x2="{sx2:.1f}" y2="{sy2:.1f}" '
                    f'stroke="{e.color}" stroke-width="1" stroke-dasharray="4,2"/>'
                )
                lines.append(
                    f'  <text x="{mx:.1f}" y="{my:.1f}" font-size="12" fill="{e.color}" '
                    f'text-anchor="middle">{val:.1f} мм</text>'
                )
            elif isinstance(e, CADArc):
                sx, sy = self.world_to_screen(e.center.x, e.center.y, width, height)
                sr = e.radius * self.scale
                sa, ea = e.start_angle, e.end_angle
                if ea < sa:
                    ea += 360
                extent = ea - sa
                large_arc = 1 if extent > 180 else 0
                sweep = 0
                x1 = sx + sr * math.cos(math.radians(sa))
                y1 = sy - sr * math.sin(math.radians(sa))
                x2 = sx + sr * math.cos(math.radians(ea))
                y2 = sy - sr * math.sin(math.radians(ea))
                lines.append(
                    f'  <path d="M {x1:.1f} {y1:.1f} '
                    f"A {sr:.1f} {sr:.1f} 0 {large_arc} {sweep} "
                    f'{x2:.1f} {y2:.1f}" '
                    f'fill="none" stroke="{e.color}" stroke-width="{e.line_width}"/>'
                )
            elif isinstance(e, CADPolyline):
                pts = []
                for p in e.points:
                    sx, sy = self.world_to_screen(p.x, p.y, width, height)
                    pts.append(f"{sx:.1f},{sy:.1f}")
                if e.closed and len(pts) > 0:
                    pts.append(pts[0])
                path_d = "M " + " L ".join(pts)
                lines.append(
                    f'  <path d="{path_d}" fill="none" stroke="{e.color}" '
                    f'stroke-width="{e.line_width}"/>'
                )
            elif isinstance(e, CADText):
                sx, sy = self.world_to_screen(e.x, e.y, width, height)
                anchor = {"left": "start", "center": "middle", "right": "end"}.get(e.align, "start")
                lines.append(
                    f'  <text x="{sx:.1f}" y="{sy:.1f}" font-size="{e.height * self.scale:.1f}" '
                    f'fill="{e.color}" text-anchor="{anchor}" '
                    f'transform="rotate({-e.angle} {sx:.1f} {sy:.1f})">{e.text}</text>'
                )
            elif isinstance(e, CADHatch):
                pts = []
                for p in e.boundary:
                    sx, sy = self.world_to_screen(p.x, p.y, width, height)
                    pts.append(f"{sx:.1f},{sy:.1f}")
                if len(pts) > 0:
                    pts.append(pts[0])
                lines.append(
                    f'  <polygon points="{" ".join(pts)}" fill="none" '
                    f'stroke="{e.color}" stroke-width="0.5" stroke-dasharray="2,2"/>'
                )
            elif isinstance(e, CADHole):
                sx, sy = self.world_to_screen(e.center.x, e.center.y, width, height)
                sr = e.radius * self.scale
                lines.append(
                    f'  <circle cx="{sx:.1f}" cy="{sy:.1f}" r="{sr:.1f}" '
                    f'fill="none" stroke="{e.color}" stroke-width="{e.line_width}"/>'
                )
                lines.append(
                    f'  <line x1="{sx-sr:.1f}" y1="{sy:.1f}" x2="{sx+sr:.1f}" y2="{sy:.1f}" '
                    f'stroke="{e.color}" stroke-width="0.5"/>'
                )
                lines.append(
                    f'  <line x1="{sx:.1f}" y1="{sy-sr:.1f}" x2="{sx:.1f}" y2="{sy+sr:.1f}" '
                    f'stroke="{e.color}" stroke-width="0.5"/>'
                )
                if e.label:
                    lines.append(
                        f'  <text x="{sx:.1f}" y="{sy-sr-5:.1f}" font-size="10" '
                        f'fill="{e.color}" text-anchor="middle">{e.label}</text>'
                    )
        lines.append("</svg>")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return filepath

    def export_dxf(self, filepath):
        lines = [
            "0",
            "SECTION",
            "2",
            "HEADER",
            "9",
            "$ACADVER",
            "1",
            "AC1009",
            "0",
            "ENDSEC",
            "0",
            "SECTION",
            "2",
            "TABLES",
            "0",
            "ENDSEC",
            "0",
            "SECTION",
            "2",
            "BLOCKS",
            "0",
            "ENDSEC",
            "0",
            "SECTION",
            "2",
            "ENTITIES",
        ]
        for e in self.get_visible_entities():
            lines.extend(["0", type(e).__name__.upper().replace("CAD", "")])
            lines.extend(["8", e.layer])
            lines.extend(["62", str(self._color_to_aci(e.color))])
            if isinstance(e, CADLine):
                lines.extend(
                    ["10", str(e.p1.x), "20", str(e.p1.y), "11", str(e.p2.x), "21", str(e.p2.y)]
                )
            elif isinstance(e, CADCircle):
                lines.extend(["10", str(e.center.x), "20", str(e.center.y), "40", str(e.radius)])
            elif isinstance(e, CADArc):
                lines.extend(
                    [
                        "10",
                        str(e.center.x),
                        "20",
                        str(e.center.y),
                        "40",
                        str(e.radius),
                        "50",
                        str(e.start_angle),
                        "51",
                        str(e.end_angle),
                    ]
                )
            elif isinstance(e, CADText):
                lines.extend(
                    [
                        "10",
                        str(e.x),
                        "20",
                        str(e.y),
                        "40",
                        str(e.height),
                        "1",
                        e.text,
                        "50",
                        str(e.angle),
                    ]
                )
            elif isinstance(e, CADPolyline):
                lines.extend(["70", "1" if e.closed else "0"])
                for p in e.points:
                    lines.extend(["0", "VERTEX", "10", str(p.x), "20", str(p.y)])
                lines.extend(["0", "SEQEND"])
            elif isinstance(e, CADRectangle):
                x1, y1 = e.p1.x, e.p1.y
                x2, y2 = e.p2.x, e.p2.y
                pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
                lines.extend(["70", "1"])
                for px, py in pts:
                    lines.extend(["0", "VERTEX", "10", str(px), "20", str(py)])
                lines.extend(["0", "SEQEND"])
        lines.extend(["0", "ENDSEC", "0", "EOF"])
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return filepath

    def _color_to_aci(self, hex_color):
        cmap = {
            "#2c3e50": 5,
            "#3498db": 5,
            "#c0392b": 1,
            "#95a5a6": 8,
            "#e67e22": 30,
            "#8e44ad": 201,
            "#27ae60": 3,
        }
        return cmap.get(hex_color, 7)

    def save_json(self, filepath):
        data = {"layers": self.layers, "entities": [], "version": "2.0"}
        for e in self.entities:
            d = {
                "type": type(e).__name__,
                "layer": e.layer,
                "color": e.color,
                "line_width": e.line_width,
            }
            if isinstance(e, CADLine | CADRectangle):
                d["p1"] = {"x": e.p1.x, "y": e.p1.y}
                d["p2"] = {"x": e.p2.x, "y": e.p2.y}
            elif isinstance(e, CADCircle):
                d["center"] = {"x": e.center.x, "y": e.center.y}
                d["radius"] = e.radius
            elif isinstance(e, CADDimension):
                d["p1"] = {"x": e.p1.x, "y": e.p1.y}
                d["p2"] = {"x": e.p2.x, "y": e.p2.y}
                d["offset"] = e.offset
                d["text"] = e.text
            elif isinstance(e, CADArc):
                d["center"] = {"x": e.center.x, "y": e.center.y}
                d["radius"] = e.radius
                d["start_angle"] = e.start_angle
                d["end_angle"] = e.end_angle
            elif isinstance(e, CADPolyline):
                d["points"] = [{"x": p.x, "y": p.y} for p in e.points]
                d["closed"] = e.closed
            elif isinstance(e, CADText):
                d["x"] = e.x
                d["y"] = e.y
                d["text"] = e.text
                d["height"] = e.height
                d["angle"] = e.angle
                d["align"] = e.align
            elif isinstance(e, CADHatch):
                d["boundary"] = [{"x": p.x, "y": p.y} for p in e.boundary]
                d["hatch_angle"] = e.hatch_angle
                d["spacing"] = e.spacing
            elif isinstance(e, CADHole):
                d["center"] = {"x": e.center.x, "y": e.center.y}
                d["radius"] = e.radius
                d["label"] = e.label
            data["entities"].append(d)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filepath

    def load_json(self, filepath):
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        self.layers = data.get("layers", self.layers)
        self.entities.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        for d in data.get("entities", []):
            e = self._entity_from_dict(d)
            if e:
                self.entities.append(e)

    def _entity_from_dict(self, d):
        t = d.get("type")
        kw = {
            "layer": d.get("layer", "0"),
            "color": d.get("color", "#2c3e50"),
            "line_width": d.get("line_width", 1),
        }
        if t == "CADLine":
            return CADLine(
                CADPoint(d["p1"]["x"], d["p1"]["y"]), CADPoint(d["p2"]["x"], d["p2"]["y"]), **kw
            )
        elif t == "CADRectangle":
            return CADRectangle(
                CADPoint(d["p1"]["x"], d["p1"]["y"]), CADPoint(d["p2"]["x"], d["p2"]["y"]), **kw
            )
        elif t == "CADCircle":
            return CADCircle(CADPoint(d["center"]["x"], d["center"]["y"]), d["radius"], **kw)
        elif t == "CADDimension":
            return CADDimension(
                CADPoint(d["p1"]["x"], d["p1"]["y"]),
                CADPoint(d["p2"]["x"], d["p2"]["y"]),
                d.get("offset", 15),
                d.get("text"),
                **kw,
            )
        elif t == "CADArc":
            return CADArc(
                CADPoint(d["center"]["x"], d["center"]["y"]),
                d["radius"],
                d["start_angle"],
                d["end_angle"],
                **kw,
            )
        elif t == "CADPolyline":
            pts = [CADPoint(p["x"], p["y"]) for p in d.get("points", [])]
            return CADPolyline(pts, d.get("closed", False), **kw)
        elif t == "CADText":
            return CADText(
                d["x"],
                d["y"],
                d.get("text", ""),
                d.get("height", 10),
                d.get("angle", 0),
                d.get("align", "left"),
                **kw,
            )
        elif t == "CADHatch":
            pts = [CADPoint(p["x"], p["y"]) for p in d.get("boundary", [])]
            return CADHatch(pts, d.get("hatch_angle", 45), d.get("spacing", 5), **kw)
        elif t == "CADHole":
            return CADHole(
                CADPoint(d["center"]["x"], d["center"]["y"]), d["radius"], d.get("label", ""), **kw
            )
        return None


# ===================== gui =====================


class _Tooltip:
    """Внутрішній клас для підказок — коротка (одразу) та довга (через 3 с)"""

    def __init__(self, widget, short_text, long_text, delay_short=300, delay_long=3000):
        self.widget = widget
        self.short_text = short_text
        self.long_text = long_text
        self.delay_short = delay_short
        self.delay_long = delay_long
        self.tip_window = None
        self.id_short = None
        self.id_long = None
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None):
        self.id_short = self.widget.after(self.delay_short, self._show_short)
        self.id_long = self.widget.after(self.delay_long, self._show_long)

    def _on_leave(self, event=None):
        for aid in (self.id_short, self.id_long):
            if aid:
                self.widget.after_cancel(aid)
        self.id_short = self.id_long = None
        self._hide()

    def _show_short(self):
        self._hide()
        self._create_tip(self.short_text, bg="#2c3e50", fg="#ecf0f1", font=("Segoe UI", 9, "bold"))

    def _show_long(self):
        self._hide()
        self._create_tip(self.long_text, bg="#fff3cd", fg="#856404", font=("Segoe UI", 9), border=1)

    def _create_tip(self, text, bg, fg, font, border=0):
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tip_window,
            text=text,
            background=bg,
            foreground=fg,
            font=font,
            relief=tk.SOLID if border else tk.FLAT,
            borderwidth=border,
            padx=8,
            pady=4,
        )
        label.pack()

    def _hide(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class CADEditorFrame(tk.Frame):
    """GUI-фрейм CAD-редактора — Покращена версія 2.0"""

    TOOLS = [
        "select",
        "line",
        "rectangle",
        "circle",
        "arc",
        "polyline",
        "dimension",
        "text",
        "hole",
        "hatch",
        "move",
        "rotate",
        "copy",
        "mirror",
        "offset",
        "trim",
        "break",
        "fillet",
        "chamfer",
        "pan",
    ]
    TOOL_ICONS = {
        "select": "🖱",
        "line": "📏",
        "rectangle": "▭",
        "circle": "○",
        "arc": "⌒",
        "polyline": "〰",
        "dimension": "📐",
        "text": "T",
        "hole": "◉",
        "hatch": "▦",
        "move": "↔",
        "rotate": "↻",
        "copy": "⎘",
        "mirror": "⇄",
        "offset": "⇥",
        "trim": "✂",
        "break": "⤨",
        "fillet": "⊃",
        "chamfer": "⊏",
        "pan": "✋",
    }
    TOOL_HINTS = {
        "select": "Клік — вибір. Drag — рамка. Ctrl+клік — додати до вибору.",
        "line": "Drag — лінія від точки до точки.",
        "rectangle": "Drag — прямокутник.",
        "circle": "Drag — коло (радіус).",
        "arc": "Клік 1 — центр, Клік 2 — радіус, Drag/Клік 3 — кут розгортки.",
        "polyline": "Клік — точка. Enter — замкнути. Esc — скасувати.",
        "dimension": "Drag — розмірна лінія.",
        "text": "Клік — розмістити текст.",
        "hole": "Drag — отвір (радіус).",
        "hatch": "Клік всередині області — штрихування.",
        "move": "Виділіть об'єкти, потім drag — переміщення.",
        "rotate": "Виділіть об'єкти, потім drag — обертання.",
        "copy": "Виділіть об'єкти, потім drag — копіювання.",
        "mirror": "Виділіть об'єкти, потім два кліки — лінія дзеркала.",
        "offset": "Клік на лінію/полілінію, потім drag — відстань.",
        "trim": "Клік на лінію біля кінця, що треба видалити.",
        "break": "Клік на лінію, потім два кліки — точки розриву.",
        "fillet": "Клік на два відрізки — скруглення.",
        "chamfer": "Клік на два відрізки — фаска.",
        "pan": "Drag — панорама.",
    }

    TOOL_NAMES = {
        "select": "Вибір",
        "line": "Лінія",
        "rectangle": "Прямокутник",
        "circle": "Коло",
        "arc": "Дуга",
        "polyline": "Полілінія",
        "dimension": "Розмір",
        "text": "Текст",
        "hole": "Отвір",
        "hatch": "Штрихування",
        "move": "Перемістити",
        "rotate": "Обертання",
        "copy": "Копіювати",
        "mirror": "Дзеркало",
        "offset": "Офсет",
        "trim": "Обрізати",
        "break": "Розірвати",
        "fillet": "Скруглення",
        "chamfer": "Фаска",
        "pan": "Панорама",
    }

    def __init__(self, parent, colors=None, **kwargs):
        super().__init__(parent, **kwargs)
        defaults = {
            "bg": "#f0f0f0",
            "fg": "#333333",
            "accent": "#3498db",
            "card": "white",
            "sidebar": "#2c3e50",
            "sidebar_fg": "white",
            "toolbar": "#34495e",
            "status": "#ecf0f1",
        }
        self.colors = {**defaults, **(colors or {})}
        self.configure(bg=self.colors["bg"])

        self.cad = CADEditor()
        self.current_tool = "select"
        self.temp_points = []
        self.preview_id = None
        self.drag_start = None
        self.drag_start_screen = None
        self.pan_start = None
        self.pan_origin = None
        self.drawing = False
        self.last_world_pos = None
        self.snap_indicator = None
        self.selection_rect_id = None
        self.clipboard = []
        self._size_preview_val = 0.0
        self._size_preview_tool = None
        self._last_drag_point = None

        self.snap_modes = {
            "grid": True,
            "ortho": False,
            "endpoint": True,
            "midpoint": False,
            "center": False,
            "intersection": False,
            "tangent": False,
        }

        self.build_ui()
        self.bind_events()

    def build_ui(self):
        toolbar = tk.Frame(self, bg=self.colors["toolbar"], height=40)
        toolbar.pack(fill=tk.X, pady=(0, 1))
        toolbar.pack_propagate(False)

        tk.Label(
            toolbar, text="🔧", bg=self.colors["toolbar"], fg="white", font=("Segoe UI", 12)
        ).pack(side=tk.LEFT, padx=(10, 5))

        self.tool_buttons = {}
        draw_tools = [
            "select",
            "line",
            "rectangle",
            "circle",
            "arc",
            "polyline",
            "dimension",
            "text",
            "hole",
            "hatch",
        ]
        edit_tools = [
            "move",
            "rotate",
            "copy",
            "mirror",
            "offset",
            "trim",
            "break",
            "fillet",
            "chamfer",
            "pan",
        ]

        for tool in draw_tools:
            btn = tk.Button(
                toolbar,
                text=f"{self.TOOL_ICONS[tool]}",
                bg=self.colors["toolbar"],
                fg="white",
                font=("Segoe UI", 10),
                bd=0,
                width=3,
                cursor="hand2",
                command=lambda t=tool: self.set_tool(t),
            )
            btn.pack(side=tk.LEFT, padx=1)
            self.tool_buttons[tool] = btn
            _Tooltip(btn, self.TOOL_NAMES[tool], self.TOOL_HINTS[tool])

        tk.Label(
            toolbar, text="│", bg=self.colors["toolbar"], fg="#7f8c8d", font=("Segoe UI", 14)
        ).pack(side=tk.LEFT, padx=5)

        for tool in edit_tools:
            btn = tk.Button(
                toolbar,
                text=f"{self.TOOL_ICONS[tool]}",
                bg=self.colors["toolbar"],
                fg="white",
                font=("Segoe UI", 10),
                bd=0,
                width=3,
                cursor="hand2",
                command=lambda t=tool: self.set_tool(t),
            )
            btn.pack(side=tk.LEFT, padx=1)
            self.tool_buttons[tool] = btn
            _Tooltip(btn, self.TOOL_NAMES[tool], self.TOOL_HINTS[tool])

        self._highlight_tool("select")

        tk.Label(
            toolbar, text="│", bg=self.colors["toolbar"], fg="#7f8c8d", font=("Segoe UI", 14)
        ).pack(side=tk.LEFT, padx=5)
        btn_undo = tk.Button(
            toolbar,
            text="↩",
            bg=self.colors["toolbar"],
            fg="#f1c40f",
            font=("Segoe UI", 12, "bold"),
            bd=0,
            width=3,
            command=self.undo,
        )
        btn_undo.pack(side=tk.LEFT)
        _Tooltip(btn_undo, "Скасувати", "Скасувати останню дію (Ctrl+Z)")
        btn_redo = tk.Button(
            toolbar,
            text="↪",
            bg=self.colors["toolbar"],
            fg="#f1c40f",
            font=("Segoe UI", 12, "bold"),
            bd=0,
            width=3,
            command=self.redo,
        )
        btn_redo.pack(side=tk.LEFT)
        _Tooltip(btn_redo, "Повернути", "Повернути скасовану дію (Ctrl+Y)")

        tk.Label(
            toolbar, text="│", bg=self.colors["toolbar"], fg="#7f8c8d", font=("Segoe UI", 14)
        ).pack(side=tk.LEFT, padx=5)
        btn_zin = tk.Button(
            toolbar,
            text="⊕",
            bg=self.colors["toolbar"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            width=3,
            command=self.zoom_in,
        )
        btn_zin.pack(side=tk.LEFT)
        _Tooltip(btn_zin, "Збільшити", "Збільшити масштаб")
        self.zoom_label = tk.Label(
            toolbar,
            text="100%",
            bg=self.colors["toolbar"],
            fg="white",
            font=("Segoe UI", 10),
            width=8,
        )
        self.zoom_label.pack(side=tk.LEFT)
        btn_zout = tk.Button(
            toolbar,
            text="⊖",
            bg=self.colors["toolbar"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            width=3,
            command=self.zoom_out,
        )
        btn_zout.pack(side=tk.LEFT)
        _Tooltip(btn_zout, "Зменшити", "Зменшити масштаб")
        btn_zrst = tk.Button(
            toolbar,
            text="⊘",
            bg=self.colors["toolbar"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            width=3,
            command=self.zoom_reset,
        )
        btn_zrst.pack(side=tk.LEFT)
        _Tooltip(btn_zrst, "Скидання масштабу", "Масштаб 100%, центрування")
        btn_zext = tk.Button(
            toolbar,
            text="⬛",
            bg=self.colors["toolbar"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            width=3,
            command=self.zoom_extents,
        )
        btn_zext.pack(side=tk.LEFT)
        _Tooltip(btn_zext, "Вмістити все", "Показати всі об'єкти у вікні")

        btn_save = tk.Button(
            toolbar,
            text="💾",
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            width=4,
            command=self.save_drawing,
        )
        btn_save.pack(side=tk.RIGHT, padx=10)
        _Tooltip(btn_save, "Зберегти", "Зберегти креслення у форматі JSON")
        btn_load = tk.Button(
            toolbar,
            text="📂",
            bg="#2980b9",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            width=4,
            command=self.load_drawing,
        )
        btn_load.pack(side=tk.RIGHT, padx=2)
        _Tooltip(btn_load, "Відкрити", "Завантажити креслення з JSON")
        btn_svg = tk.Button(
            toolbar,
            text="🖼",
            bg="#8e44ad",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            width=4,
            command=self.export_svg,
        )
        btn_svg.pack(side=tk.RIGHT, padx=2)
        _Tooltip(btn_svg, "Експорт SVG", "Експортувати креслення у SVG")
        btn_dxf = tk.Button(
            toolbar,
            text="📄",
            bg="#16a085",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            width=4,
            command=self.export_dxf,
        )
        btn_dxf.pack(side=tk.RIGHT, padx=2)
        _Tooltip(btn_dxf, "Експорт DXF", "Експортувати креслення у DXF")

        # --- КНОПКА FREECAD ---
        fcad_color = "#1f4e79" if FREECAD_AVAILABLE else "#7f8c8d"
        btn_freecad = tk.Button(
            toolbar,
            text="🏗",
            bg=fcad_color,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            width=4,
            command=self.export_freecad,
        )
        btn_freecad.pack(side=tk.RIGHT, padx=2)
        if FREECAD_AVAILABLE:
            _Tooltip(btn_freecad, "Експорт FreeCAD", "Експортувати креслення у FreeCAD .FCStd")
        else:
            _Tooltip(btn_freecad, "FreeCAD недоступний", "Встановіть FreeCAD для 3D експорту")
        btn_clear = tk.Button(
            toolbar,
            text="🗑",
            bg="#c0392b",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            width=4,
            command=self.clear_drawing,
        )
        btn_clear.pack(side=tk.RIGHT, padx=2)
        _Tooltip(btn_clear, "Очистити", "Очистити все креслення")

        main = tk.Frame(self, bg=self.colors["bg"])
        main.pack(fill=tk.BOTH, expand=True)

        canvas_frame = tk.Frame(main, bg=self.colors["bg"], bd=1, relief=tk.SUNKEN)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)

        self.canvas = tk.Canvas(canvas_frame, bg="#ffffff", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        cvsb = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        cvsb.pack(side=tk.RIGHT, fill="y")
        chsb = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        chsb.pack(side=tk.BOTTOM, fill="x")
        self.canvas.configure(yscrollcommand=cvsb.set, xscrollcommand=chsb.set)

        right = tk.Frame(main, bg=self.colors["card"], width=250, bd=1, relief=tk.RIDGE)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 4), pady=4)
        right.pack_propagate(False)

        coord_frame = tk.LabelFrame(
            right,
            text="📍 Координати",
            bg=self.colors["card"],
            fg=self.colors["fg"],
            font=("Segoe UI", 10, "bold"),
            padx=8,
            pady=8,
        )
        coord_frame.pack(fill=tk.X, padx=8, pady=(8, 4))
        self.coord_label = tk.Label(
            coord_frame,
            text="X: 0.0  Y: 0.0",
            bg=self.colors["card"],
            fg=self.colors["fg"],
            font=("Segoe UI", 10, "bold"),
        )
        self.coord_label.pack()
        self.snap_label = tk.Label(
            coord_frame,
            text="Snap: grid",
            bg=self.colors["card"],
            fg="#27ae60",
            font=("Segoe UI", 8),
        )
        self.snap_label.pack()

        snap_frame = tk.LabelFrame(
            right,
            text="⚙️ Прив'язка (Snap)",
            bg=self.colors["card"],
            fg=self.colors["fg"],
            font=("Segoe UI", 10, "bold"),
            padx=8,
            pady=8,
        )
        snap_frame.pack(fill=tk.X, padx=8, pady=4)
        self.snap_vars = {}
        snap_items = [
            ("grid", "Сітка (Grid)", True),
            ("ortho", "Орто (F8)", False),
            ("endpoint", "Кінець лінії", True),
            ("midpoint", "Середина", False),
            ("center", "Центр", False),
            ("intersection", "Перетин", False),
            ("tangent", "Дотична", False),
        ]
        for key, label, default in snap_items:
            var = tk.BooleanVar(value=default)
            self.snap_vars[key] = var
            self.snap_modes[key] = default
            cb = tk.Checkbutton(
                snap_frame,
                text=label,
                variable=var,
                bg=self.colors["card"],
                font=("Segoe UI", 10),
                command=lambda k=key, v=var: self._update_snap(k, v),
            )
            cb.pack(anchor=tk.W, pady=1)

        tk.Label(
            snap_frame, text="Крок сітки (мм):", bg=self.colors["card"], font=("Segoe UI", 10)
        ).pack(anchor=tk.W, pady=(5, 2))
        self.grid_entry = tk.Entry(snap_frame, width=10, font=("Segoe UI", 10))
        self.grid_entry.insert(0, "10")
        self.grid_entry.pack(anchor=tk.W)
        tk.Button(
            snap_frame,
            text="Застосувати",
            bg=self.colors["accent"],
            fg="white",
            font=("Segoe UI", 9),
            command=self.apply_grid,
        ).pack(anchor=tk.W, pady=5)

        self.prop_frame = tk.LabelFrame(
            right,
            text="📋 Властивості",
            bg=self.colors["card"],
            fg=self.colors["fg"],
            font=("Segoe UI", 10, "bold"),
            padx=8,
            pady=8,
        )
        self.prop_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.prop_text = tk.Text(
            self.prop_frame,
            wrap="word",
            font=("Segoe UI", 9),
            bg="#fafafa",
            relief=tk.FLAT,
            height=10,
            state="disabled",
        )
        self.prop_text.pack(fill=tk.BOTH, expand=True)

        layer_frame = tk.LabelFrame(
            right,
            text="🗂️ Шари",
            bg=self.colors["card"],
            fg=self.colors["fg"],
            font=("Segoe UI", 10, "bold"),
            padx=8,
            pady=8,
        )
        layer_frame.pack(fill=tk.X, padx=8, pady=4)
        self.layer_vars = {}
        for layer_name, layer_data in self.cad.layers.items():
            var = tk.BooleanVar(value=layer_data["visible"])
            self.layer_vars[layer_name] = var
            row = tk.Frame(layer_frame, bg=self.colors["card"])
            row.pack(fill=tk.X, pady=1)
            tk.Checkbutton(
                row,
                variable=var,
                bg=self.colors["card"],
                command=lambda _layer=layer_name: self.toggle_layer(_layer),
            ).pack(side=tk.LEFT)
            tk.Label(
                row,
                text=f"{layer_data['name']} ({layer_name})",
                bg=self.colors["card"],
                fg=layer_data["color"],
                font=("Segoe UI", 9),
            ).pack(side=tk.LEFT, padx=5)

        bottom = tk.Frame(self, bg=self.colors["status"], height=32, bd=1, relief=tk.RIDGE)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)
        bottom.pack_propagate(False)

        tk.Label(bottom, text="Координати:", bg=self.colors["status"], font=("Segoe UI", 9)).pack(
            side=tk.LEFT, padx=(10, 2)
        )
        self.coord_entry = tk.Entry(bottom, width=20, font=("Segoe UI", 9))
        self.coord_entry.pack(side=tk.LEFT, padx=2)
        self.coord_entry.bind("<Return>", self.on_coord_entry)
        self.coord_entry.insert(0, "X,Y")
        self.coord_entry.config(fg="gray")
        self.coord_entry.bind("<FocusIn>", lambda e: self._on_entry_focus_in())
        self.coord_entry.bind("<FocusOut>", lambda e: self._on_entry_focus_out())

        tk.Button(
            bottom,
            text="↵ Ввести",
            bg=self.colors["accent"],
            fg="white",
            font=("Segoe UI", 8),
            command=lambda: self.on_coord_entry(None),
        ).pack(side=tk.LEFT, padx=2)

        tk.Label(
            bottom, text="│", bg=self.colors["status"], fg="#7f8c8d", font=("Segoe UI", 9)
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(bottom, text="Розмір:", bg=self.colors["status"], font=("Segoe UI", 9)).pack(
            side=tk.LEFT, padx=(2, 0)
        )
        self.size_entry = tk.Entry(bottom, width=12, font=("Segoe UI", 9), state="disabled")
        self.size_entry.pack(side=tk.LEFT, padx=2)
        self.size_entry.bind("<Return>", self.on_size_entry)
        tk.Button(
            bottom,
            text="↵ Застосувати",
            bg=self.colors["accent"],
            fg="white",
            font=("Segoe UI", 8),
            command=lambda: self.on_size_entry(None),
        ).pack(side=tk.LEFT, padx=2)

        self.status_label = tk.Label(
            bottom,
            text="Готово — клікніть для початку креслення",
            bg=self.colors["status"],
            fg="#666",
            font=("Segoe UI", 9),
        )
        self.status_label.pack(side=tk.LEFT, padx=(20, 0))

        self.undo_label = tk.Label(
            bottom, text="", bg=self.colors["status"], fg="#7f8c8d", font=("Segoe UI", 8)
        )
        self.undo_label.pack(side=tk.RIGHT, padx=10)

        self.draw_grid()

    def _on_entry_focus_in(self):
        if self.coord_entry.get() == "X,Y":
            self.coord_entry.delete(0, tk.END)
            self.coord_entry.config(fg="black")

    def _on_entry_focus_out(self):
        if not self.coord_entry.get():
            self.coord_entry.insert(0, "X,Y")
            self.coord_entry.config(fg="gray")

    def _update_snap(self, key, var):
        self.snap_modes[key] = var.get()
        active = [k for k, v in self.snap_modes.items() if v]
        self.snap_label.config(
            text=f"Snap: {', '.join(active[:3])}{'...' if len(active) > 3 else ''}"
        )

    def _highlight_tool(self, tool):
        for t, btn in self.tool_buttons.items():
            if t == tool:
                btn.configure(bg=self.colors["accent"], fg="white")
            else:
                btn.configure(bg=self.colors["toolbar"], fg="white")

    def set_tool(self, tool):
        self.current_tool = tool
        self.temp_points = []
        self.drawing = False
        self._highlight_tool(tool)
        self.status_label.config(text=self.TOOL_HINTS.get(tool, tool.capitalize()))
        if tool in ("pan",):
            self.canvas.config(cursor="fleur")
        elif tool == "select":
            self.canvas.config(cursor="")
        else:
            self.canvas.config(cursor="crosshair")

    def apply_grid(self):
        try:
            val = float(self.grid_entry.get())
            if val > 0:
                self.cad.grid_size = val
                self.cad.snap_size = val
                self.draw_grid()
        except ValueError:
            pass

    def toggle_layer(self, layer_name):
        self.cad.layers[layer_name]["visible"] = self.layer_vars[layer_name].get()
        self.redraw()

    def zoom_in(self):
        self.cad.scale *= 1.2
        self._update_zoom_label()
        self.redraw()

    def zoom_out(self):
        self.cad.scale *= 0.8
        self._update_zoom_label()
        self.redraw()

    def zoom_reset(self):
        self.cad.scale = 1.0
        self.cad.origin_x = 0
        self.cad.origin_y = 0
        self._update_zoom_label()
        self.redraw()

    def zoom_extents(self):
        if not self.cad.entities:
            return
        bboxes = [e.get_cached_bbox() for e in self.cad.entities]
        min_x = min(b[0] for b in bboxes)
        min_y = min(b[1] for b in bboxes)
        max_x = max(b[2] for b in bboxes)
        max_y = max(b[3] for b in bboxes)
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10:
            self.after(100, self.zoom_extents)
            return
        dx = max_x - min_x if max_x > min_x else 1
        dy = max_y - min_y if max_y > min_y else 1
        margin = 1.2
        scale_x = (w / margin) / dx
        scale_y = (h / margin) / dy
        self.cad.scale = min(scale_x, scale_y)
        self.cad.origin_x = (min_x + max_x) / 2
        self.cad.origin_y = (min_y + max_y) / 2
        self._update_zoom_label()
        self.redraw()

    def _update_zoom_label(self):
        self.zoom_label.config(text=f"{int(self.cad.scale * 100)}%")
        self._update_undo_label()

    def _update_undo_label(self):
        undo_text = ""
        if self.cad.can_undo():
            undo_text = f"↩ {str(self.cad.undo_stack[-1])}"
        self.undo_label.config(text=undo_text)

    def undo(self):
        if self.cad.undo():
            self.redraw()
            self.update_properties()
            self._update_undo_label()
            self.status_label.config(text="Скасовано")

    def redo(self):
        if self.cad.redo():
            self.redraw()
            self.update_properties()
            self._update_undo_label()
            self.status_label.config(text="Повернуто")

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<MouseWheel>", self.on_wheel)
        self.canvas.bind("<Button-2>", self.on_middle_down)
        self.canvas.bind("<B2-Motion>", self.on_middle_drag)
        self.canvas.bind("<ButtonRelease-2>", self.on_middle_up)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.bind("<Key>", self.on_key)
        self.focus_set()

    def on_key(self, event):
        if event.state & 0x4 and event.keysym.lower() == "z":
            self.undo()
            return
        if event.state & 0x4 and event.keysym.lower() == "y":
            self.redo()
            return
        if event.state & 0x4 and event.keysym.lower() == "a":
            self.cad.select_all()
            self.redraw()
            self.update_properties()
            return
        if event.state & 0x4 and event.keysym.lower() == "c":
            self.clipboard = self.cad.copy_selected()
            self.status_label.config(text=f"Скопійовано {len(self.clipboard)} об'єктів")
            return
        if event.state & 0x4 and event.keysym.lower() == "v":
            self.paste_clipboard()
            return
        if event.keysym == "Delete":
            self.cad.delete_selected()
            self.redraw()
            self.update_properties()
            self._update_undo_label()
        elif event.keysym == "Escape":
            self.cancel_current()
        elif event.keysym in ("Return", "KP_Enter"):
            if self.current_tool == "polyline" and self.drawing:
                self._finish_polyline()
        elif event.keysym.lower() == "l":
            self.set_tool("line")
        elif event.keysym.lower() == "r":
            self.set_tool("rectangle")
        elif event.keysym.lower() == "c":
            self.set_tool("circle")
        elif event.keysym.lower() == "a":
            self.set_tool("arc")
        elif event.keysym.lower() == "p":
            self.set_tool("polyline")
        elif event.keysym.lower() == "t":
            self.set_tool("text")
        elif event.keysym.lower() == "d":
            self.set_tool("dimension")
        elif event.keysym.lower() == "h":
            self.set_tool("hole")
        elif event.keysym.lower() == "s":
            self.set_tool("select")
        elif event.keysym.lower() == "m":
            self.set_tool("move")
        elif event.keysym.lower() == "o":
            self.set_tool("offset")
        elif event.keysym.lower() == "f":
            self.set_tool("fillet")
        elif event.keysym.lower() == "v":
            if not (event.state & 0x4):
                self.set_tool("chamfer")
        elif event.keysym.lower() == "b":
            self.set_tool("break")
        elif event.keysym.lower() == "n":
            self.set_tool("trim")
        elif event.keysym == "F8":
            self.snap_vars["ortho"].set(not self.snap_modes["ortho"])
            self._update_snap("ortho", self.snap_vars["ortho"])

    def cancel_current(self):
        self.temp_points = []
        self.drawing = False
        self.drag_start = None
        self.drag_start_screen = None
        self.canvas.delete("preview")
        self.canvas.delete("snap_marker")
        self.canvas.delete("selection_rect")
        self.selection_rect_id = None
        self.cad.deselect_all()
        self.redraw()
        self.set_tool("select")
        self.status_label.config(text="Скасовано")
        self._clear_size_entry()
        self._last_drag_point = None

    def paste_clipboard(self):
        if not self.clipboard:
            return
        for e in self.clipboard:
            copy = e.copy_entity()
            copy.move(20, -20)
            self.cad.execute_command(AddEntityCmd(copy))
        self.redraw()
        self.update_properties()
        self._update_undo_label()
        self.status_label.config(text=f"Вставлено {len(self.clipboard)} об'єктів")

    def _get_world_pos(self, event):
        sx, sy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        return self.cad.screen_to_world(sx, sy, w, h)

    def _get_snapped_pos(self, event, base_point=None):
        wx, wy = self._get_world_pos(event)
        p, stype = self.cad.snap_point(
            wx,
            wy,
            self.snap_modes,
            self.cad.get_visible_entities(),
            self.canvas.winfo_width(),
            self.canvas.winfo_height(),
        )
        if base_point and self.snap_modes.get("ortho", False):
            p = self.cad.apply_ortho(base_point.x, base_point.y, p.x, p.y)
            stype = "ortho"
        return p, stype

    def _draw_snap_marker(self, p, stype):
        self.canvas.delete("snap_marker")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        sx, sy = self.cad.world_to_screen(p.x, p.y, w, h)
        r = 6
        colors = {
            "grid": "#3498db",
            "ortho": "#e67e22",
            "endpoint": "#27ae60",
            "midpoint": "#9b59b6",
            "center": "#e74c3c",
            "quadrant": "#f39c12",
            "insert": "#8e44ad",
            "free": "#95a5a6",
        }
        color = colors.get(stype, "#3498db")
        self.canvas.create_oval(
            sx - r, sy - r, sx + r, sy + r, outline=color, width=2, tags="snap_marker"
        )
        self.canvas.create_line(sx - r - 4, sy, sx + r + 4, sy, fill=color, tags="snap_marker")
        self.canvas.create_line(sx, sy - r - 4, sx, sy + r + 4, fill=color, tags="snap_marker")
        self.snap_label.config(text=f"Snap: {stype}", fg=color)

    # ------------------------------------------------------------------
    # Обробники подій миші
    # ------------------------------------------------------------------
    def on_motion(self, event):
        wx, wy = self._get_world_pos(event)
        self.last_world_pos = (wx, wy)
        self.coord_label.config(text=f"X: {wx:.2f}  Y: {wy:.2f}")
        p, stype = self._get_snapped_pos(event)
        self._draw_snap_marker(p, stype)

    def on_click(self, event):
        self.focus_set()
        p, stype = self._get_snapped_pos(event)
        tool = self.current_tool

        if tool == "select":
            add = bool(event.state & 0x4)  # Ctrl
            ent = self.cad.select_at(p.x, p.y, tol=5, add=add)
            if ent:
                self.status_label.config(text=f"Вибрано: {type(ent).__name__} #{ent.id}")
            else:
                self.drag_start = p
                self.drag_start_screen = (
                    self.canvas.canvasx(event.x),
                    self.canvas.canvasy(event.y),
                )
            self.redraw()
            self.update_properties()

        elif tool in ("line", "rectangle", "circle", "dimension", "hole"):
            if not self.drawing:
                self.drag_start = p
                self.drawing = True
                self.status_label.config(text=f"{tool}: drag та відпустіть для завершення")
        elif tool == "arc":
            if len(self.temp_points) == 0:
                self.temp_points.append(p)
                self.drawing = True
                self.status_label.config(text="Arc: клікніть початкову точку (радіус)")
            elif len(self.temp_points) == 1:
                self.temp_points.append(p)
                self.status_label.config(text="Arc: drag або клік для куту розгортки")
            elif len(self.temp_points) == 2:
                self._finish_arc_cse(p)

        elif tool == "polyline":
            self.temp_points.append(p)
            self.drawing = True
            self.status_label.config(
                text=f"Полілінія: {len(self.temp_points)} точок. Enter — замкнути, Esc — скасувати"
            )
            self.redraw()

        elif tool == "text":
            self._ask_text(p)

        elif tool == "hatch":
            self._create_hatch_at(p)

        elif tool in ("move", "copy"):
            sel = self.cad.get_selected()
            if sel and not self.drawing:
                self.drag_start = p
                self.drawing = True
                self.status_label.config(text=f"{tool.capitalize()}: drag та відпустіть")

        elif tool == "rotate":
            sel = self.cad.get_selected()
            if sel and not self.drawing:
                self.drag_start = p
                self.drawing = True
                self.status_label.config(text="Rotate: drag для кута обертання")

        elif tool == "mirror":
            sel = self.cad.get_selected()
            if sel:
                if len(self.temp_points) == 0:
                    self.temp_points.append(p)
                    self.status_label.config(text="Mirror: вкажіть другу точку лінії дзеркала")
                else:
                    p1 = self.temp_points[0]
                    self.cad.mirror_selected(p1.x, p1.y, p.x, p.y)
                    self.temp_points = []
                    self.redraw()
                    self._update_undo_label()
                    self.status_label.config(text="Відображено")

        elif tool == "offset":
            ent = self.cad.select_at(p.x, p.y, tol=5, add=False)
            if isinstance(ent, CADLine | CADPolyline):
                if isinstance(ent, CADLine):
                    x1, y1, x2, y2 = offset_line(ent.p1.x, ent.p1.y, ent.p2.x, ent.p2.y, 10)
                    if x1 is not None:
                        new_line = CADLine(
                            CADPoint(x1, y1),
                            CADPoint(x2, y2),
                            layer=ent.layer,
                            color=ent.color,
                            line_width=ent.line_width,
                        )
                        self.cad.add_entity(new_line)
                elif isinstance(ent, CADPolyline):
                    new_poly = ent.offset(10)
                    if new_poly:
                        self.cad.add_entity(new_poly)
                self.redraw()
                self._update_undo_label()
                self.status_label.config(text="Офсет створено")

        elif tool == "trim":
            ent = self.cad.select_at(p.x, p.y, tol=5, add=False)
            if ent:
                self.cad.delete_entity(ent)
                self.redraw()
                self._update_undo_label()
                self.status_label.config(text="Об'єкт видалено (trim)")

        elif tool == "break":
            ent = self.cad.select_at(p.x, p.y, tol=5, add=False)
            if isinstance(ent, CADLine):
                px, py = p.x, p.y
                x1, y1 = ent.p1.x, ent.p1.y
                x2, y2 = ent.p2.x, ent.p2.y
                dx, dy = x2 - x1, y2 - y1
                len2 = dx * dx + dy * dy
                if len2 > 0:
                    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / len2))
                    mx = x1 + t * dx
                    my = y1 + t * dy
                    if 0 < t < 1:
                        mid = CADPoint(mx, my)
                        l1 = CADLine(
                            ent.p1.copy(),
                            mid,
                            layer=ent.layer,
                            color=ent.color,
                            line_width=ent.line_width,
                        )
                        l2 = CADLine(
                            mid,
                            ent.p2.copy(),
                            layer=ent.layer,
                            color=ent.color,
                            line_width=ent.line_width,
                        )
                        self.cad.delete_entity(ent)
                        self.cad.add_entity(l1)
                        self.cad.add_entity(l2)
                        self.redraw()
                        self._update_undo_label()
                        self.status_label.config(text="Лінію розірвано")

        elif tool == "fillet":
            self.status_label.config(text="Fillet: виберіть два відрізки (не реалізовано повністю)")

        elif tool == "chamfer":
            self.status_label.config(
                text="Chamfer: виберіть два відрізки (не реалізовано повністю)"
            )

        elif tool == "pan":
            self.pan_start = (event.x, event.y)
            self.pan_origin = (self.cad.origin_x, self.cad.origin_y)

    def on_drag(self, event):
        base = self.drag_start if self.drawing else None
        p, stype = self._get_snapped_pos(event, base_point=base)
        self._draw_snap_marker(p, stype)

        if (
            self.current_tool in ("line", "rectangle", "circle", "dimension", "hole")
            and self.drawing
        ):
            self._update_preview(p)
            self._update_size_entry(p)
            self._last_drag_point = p
        elif self.current_tool == "arc" and self.drawing and len(self.temp_points) == 2:
            self._update_preview_arc_cse(p)
            self._last_drag_point = p
        elif self.current_tool == "select" and self.drag_start:
            self._update_selection_rect(event)
        elif self.current_tool == "pan" and self.pan_start:
            self._do_pan(event)

    def on_release(self, event):
        print("[DEBUG] on_release called, tool=", self.current_tool, "drawing=", self.drawing)
        base = self.drag_start if self.drawing else None
        p, stype = self._get_snapped_pos(event, base_point=base)
        tool = self.current_tool

        if tool in ("line", "rectangle", "circle", "dimension", "hole") and self.drawing:
            self._finish_shape(p)
        elif tool == "arc" and self.drawing and len(self.temp_points) == 2:
            self._finish_arc_cse(p)

        elif tool in ("move", "copy") and self.drawing:
            dx = p.x - self.drag_start.x
            dy = p.y - self.drag_start.y
            if tool == "move":
                self.cad.move_selected(dx, dy)
                self.status_label.config(text="Переміщено")
            else:
                copies = self.cad.copy_selected()
                for c in copies:
                    c.move(dx, dy)
                    self.cad.execute_command(AddEntityCmd(c))
                self.status_label.config(text="Скопійовано")
            self.drawing = False
            self.drag_start = None
            self.redraw()
            self._update_undo_label()

        elif tool == "rotate" and self.drawing:
            angle = math.degrees(math.atan2(p.y - self.drag_start.y, p.x - self.drag_start.x))
            self.cad.rotate_selected(self.drag_start.x, self.drag_start.y, angle)
            self.drawing = False
            self.drag_start = None
            self.redraw()
            self._update_undo_label()
            self.status_label.config(text=f"Обернуто на {angle:.1f}°")

        elif tool == "select" and self.drag_start:
            x1, y1 = self.drag_start.x, self.drag_start.y
            x2, y2 = p.x, p.y
            if abs(x2 - x1) > 1 or abs(y2 - y1) > 1:
                self.cad.select_in_rect(x1, y1, x2, y2, add=False)
                self.redraw()
                self.update_properties()
            self.drag_start = None
            self.drag_start_screen = None
            self.canvas.delete("selection_rect")

        elif tool == "pan" and self.pan_start:
            self.pan_start = None
            self.pan_origin = None

        self._clear_size_entry()

    def on_right_click(self, event):
        self.cancel_current()

    def on_wheel(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def on_middle_down(self, event):
        self.pan_start = (event.x, event.y)
        self.pan_origin = (self.cad.origin_x, self.cad.origin_y)
        self.canvas.config(cursor="fleur")

    def on_middle_drag(self, event):
        if self.pan_start:
            self._do_pan(event)

    def on_middle_up(self, event):
        self.pan_start = None
        self.pan_origin = None
        self.canvas.config(cursor="crosshair" if self.current_tool != "select" else "")

    def on_double_click(self, event):
        if self.current_tool == "polyline" and self.drawing:
            self._finish_polyline()

    # ------------------------------------------------------------------
    # Прев'ю / допоміжні малювання
    # ------------------------------------------------------------------
    def _update_preview(self, p):
        self.canvas.delete("preview")
        if not self.drag_start:
            return
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        sx1, sy1 = self.cad.world_to_screen(self.drag_start.x, self.drag_start.y, w, h)
        sx2, sy2 = self.cad.world_to_screen(p.x, p.y, w, h)
        color = self.colors["accent"]

        if self.current_tool == "line":
            self.canvas.create_line(
                sx1, sy1, sx2, sy2, fill=color, width=2, tags="preview", dash=(4, 4)
            )
        elif self.current_tool == "rectangle":
            self.canvas.create_rectangle(
                sx1, sy1, sx2, sy2, outline=color, width=2, tags="preview", dash=(4, 4)
            )
        elif self.current_tool == "circle":
            r = math.hypot(p.x - self.drag_start.x, p.y - self.drag_start.y) * self.cad.scale
            self.canvas.create_oval(
                sx1 - r,
                sy1 - r,
                sx1 + r,
                sy1 + r,
                outline=color,
                width=2,
                tags="preview",
                dash=(4, 4),
            )
        elif self.current_tool == "dimension":
            self.canvas.create_line(
                sx1, sy1, sx2, sy2, fill=color, width=2, tags="preview", dash=(4, 4)
            )
            val = math.hypot(p.x - self.drag_start.x, p.y - self.drag_start.y)
            mx, my = (sx1 + sx2) / 2, (sy1 + sy2) / 2 - 10
            self.canvas.create_text(mx, my, text=f"{val:.1f} мм", fill=color, tags="preview")
        elif self.current_tool == "hole":
            r = math.hypot(p.x - self.drag_start.x, p.y - self.drag_start.y) * self.cad.scale
            self.canvas.create_oval(
                sx1 - r,
                sy1 - r,
                sx1 + r,
                sy1 + r,
                outline=color,
                width=2,
                tags="preview",
                dash=(4, 4),
            )
            self.canvas.create_line(sx1 - r, sy1, sx1 + r, sy1, fill=color, tags="preview")
            self.canvas.create_line(sx1, sy1 - r, sx1, sy1 + r, fill=color, tags="preview")

    def _update_preview_arc_cse(self, p):
        """Прев'ю для Center-Start-End дуги"""
        self.canvas.delete("preview")
        if len(self.temp_points) != 2:
            return
        center = self.temp_points[0]
        start = self.temp_points[1]
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        scx, scy = self.cad.world_to_screen(center.x, center.y, w, h)
        sr = math.hypot(start.x - center.x, start.y - center.y) * self.cad.scale
        ssx, ssy = self.cad.world_to_screen(start.x, start.y, w, h)
        color = self.colors["accent"]

        # Центр
        self.canvas.create_oval(scx - 3, scy - 3, scx + 3, scy + 3, fill=color, tags="preview")
        # Радіус
        self.canvas.create_line(
            scx, scy, ssx, ssy, fill=color, width=1, tags="preview", dash=(4, 4)
        )
        # Початок
        self.canvas.create_oval(ssx - 3, ssy - 3, ssx + 3, ssy + 3, fill=color, tags="preview")

        # Дуга — знаковий extent
        start_angle = math.degrees(math.atan2(start.y - center.y, start.x - center.x))
        end_angle = math.degrees(math.atan2(p.y - center.y, p.x - center.x))
        extent = end_angle - start_angle
        if abs(extent) < 0.5:
            extent = 1 if extent >= 0 else -1
        n = max(2, int(abs(extent) / 5) + 1)
        pts = []
        for i in range(n + 1):
            ang = start_angle + extent * i / n
            rad = math.radians(ang)
            px = scx + sr * math.cos(rad)
            py = scy - sr * math.sin(rad)
            pts.extend([px, py])
        self.canvas.create_line(pts, fill=color, width=2, tags="preview", dash=(4, 4))

    def _finish_arc_cse(self, p):
        """Завершити Center-Start-End дугу"""
        if len(self.temp_points) != 2:
            return
        center = self.temp_points[0]
        start = self.temp_points[1]
        r = math.hypot(start.x - center.x, start.y - center.y)
        if r <= 0:
            self.temp_points = []
            self.drawing = False
            return
        start_angle = math.degrees(math.atan2(start.y - center.y, start.x - center.x))
        end_angle = math.degrees(math.atan2(p.y - center.y, p.x - center.x))
        # Зберігаємо знаковий extent — дуга йде від start_angle до end_angle
        entity = CADArc(center, r, start_angle, end_angle)
        self.cad.add_entity(entity)
        self.status_label.config(text="Дугу додано — вкажіть точний радіус")
        self.temp_points = []
        self.drawing = False
        self.drag_start = None
        self._last_drag_point = None
        self.canvas.delete("preview")
        self.redraw()
        self._update_undo_label()
        self._clear_size_entry()
        self._show_size_dialog(entity, "arc", center, start)

    def _update_selection_rect(self, event):
        self.canvas.delete("selection_rect")
        sx, sy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        x1, y1 = self.drag_start_screen
        self.canvas.create_rectangle(
            x1, y1, sx, sy, outline="#3498db", width=1, dash=(2, 2), tags="selection_rect"
        )

    def _do_pan(self, event):
        dx = event.x - self.pan_start[0]
        dy = event.y - self.pan_start[1]
        self.cad.origin_x = self.pan_origin[0] - dx / self.cad.scale
        self.cad.origin_y = self.pan_origin[1] + dy / self.cad.scale
        self.redraw()

    # ------------------------------------------------------------------
    # Малювання сітки та сутностей
    # ------------------------------------------------------------------
    def draw_grid(self):
        self.canvas.delete("grid")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10:
            self.after(100, self.draw_grid)
            return

        gs = self.cad.grid_size
        wx1, wy1 = self.cad.screen_to_world(0, 0, w, h)
        wx2, wy2 = self.cad.screen_to_world(w, h, w, h)

        x_start = math.floor(min(wx1, wx2) / gs) * gs
        x_end = math.ceil(max(wx1, wx2) / gs) * gs
        y_start = math.floor(min(wy1, wy2) / gs) * gs
        y_end = math.ceil(max(wy1, wy2) / gs) * gs

        for x in self._frange(x_start, x_end + gs / 2, gs):
            sx1, sy1 = self.cad.world_to_screen(x, y_start, w, h)
            sx2, sy2 = self.cad.world_to_screen(x, y_end, w, h)
            self.canvas.create_line(sx1, sy1, sx2, sy2, fill="#e0e0e0", tags="grid")
        for y in self._frange(y_start, y_end + gs / 2, gs):
            sx1, sy1 = self.cad.world_to_screen(x_start, y, w, h)
            sx2, sy2 = self.cad.world_to_screen(x_end, y, w, h)
            self.canvas.create_line(sx1, sy1, sx2, sy2, fill="#e0e0e0", tags="grid")

        ox, oy = self.cad.world_to_screen(0, 0, w, h)
        self.canvas.create_line(ox, 0, ox, h, fill="#bdc3c7", width=1, tags="grid")
        self.canvas.create_line(0, oy, w, oy, fill="#bdc3c7", width=1, tags="grid")

    def _frange(self, start, stop, step):
        while start <= stop:
            yield start
            start += step

    def redraw(self):
        self.canvas.delete("entity", "preview", "snap_marker", "selection_rect")
        self.draw_grid()
        for e in self.cad.get_visible_entities():
            self._draw_entity(e)
        # тимчасові точки полілінії
        if self.current_tool == "polyline" and self.temp_points:
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            pts = []
            for p in self.temp_points:
                sx, sy = self.cad.world_to_screen(p.x, p.y, w, h)
                pts.append((sx, sy))
                self.canvas.create_oval(
                    sx - 3, sy - 3, sx + 3, sy + 3, fill=self.colors["accent"], tags="preview"
                )
            for i in range(len(pts) - 1):
                self.canvas.create_line(
                    pts[i][0],
                    pts[i][1],
                    pts[i + 1][0],
                    pts[i + 1][1],
                    fill=self.colors["accent"],
                    width=2,
                    tags="preview",
                )

        # тимчасові точки дуги (center-start-end)
        if self.current_tool == "arc" and self.temp_points:
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            for p in self.temp_points:
                sx, sy = self.cad.world_to_screen(p.x, p.y, w, h)
                self.canvas.create_oval(
                    sx - 3, sy - 3, sx + 3, sy + 3, fill=self.colors["accent"], tags="preview"
                )
            if len(self.temp_points) == 2:
                s0 = self.cad.world_to_screen(self.temp_points[0].x, self.temp_points[0].y, w, h)
                s1 = self.cad.world_to_screen(self.temp_points[1].x, self.temp_points[1].y, w, h)
                self.canvas.create_line(
                    s0[0],
                    s0[1],
                    s1[0],
                    s1[1],
                    fill=self.colors["accent"],
                    width=2,
                    tags="preview",
                    dash=(4, 4),
                )

    def _draw_entity(self, e):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        color = e.color
        width = e.line_width
        if e.selected:
            color = "#e74c3c"
            width = max(width, 2)
        dash = None
        if e.layer == "CENTER":
            dash = (8, 4)

        if isinstance(e, CADLine):
            sx1, sy1 = self.cad.world_to_screen(e.p1.x, e.p1.y, w, h)
            sx2, sy2 = self.cad.world_to_screen(e.p2.x, e.p2.y, w, h)
            self.canvas.create_line(
                sx1, sy1, sx2, sy2, fill=color, width=width, tags="entity", dash=dash
            )

        elif isinstance(e, CADRectangle):
            sx1, sy1 = self.cad.world_to_screen(e.p1.x, e.p1.y, w, h)
            sx2, sy2 = self.cad.world_to_screen(e.p2.x, e.p2.y, w, h)
            self.canvas.create_rectangle(
                min(sx1, sx2),
                min(sy1, sy2),
                max(sx1, sx2),
                max(sy1, sy2),
                outline=color,
                width=width,
                tags="entity",
                dash=dash,
            )

        elif isinstance(e, CADCircle):
            sx, sy = self.cad.world_to_screen(e.center.x, e.center.y, w, h)
            sr = e.radius * self.cad.scale
            self.canvas.create_oval(
                sx - sr,
                sy - sr,
                sx + sr,
                sy + sr,
                outline=color,
                width=width,
                tags="entity",
                dash=dash,
            )

        elif isinstance(e, CADArc):
            sx, sy = self.cad.world_to_screen(e.center.x, e.center.y, w, h)
            sr = e.radius * self.cad.scale
            sa, ea = e.start_angle, e.end_angle
            extent = ea - sa  # знаковий: + = проти годинникової, - = за
            if abs(extent) < 0.5:
                extent = 1 if extent >= 0 else -1
            n = max(2, int(abs(extent) / 5) + 1)
            pts = []
            for i in range(n + 1):
                ang = sa + extent * i / n
                rad = math.radians(ang)
                px = sx + sr * math.cos(rad)
                py = sy - sr * math.sin(rad)
                pts.extend([px, py])
            self.canvas.create_line(pts, fill=color, width=width, tags="entity", dash=dash)

        elif isinstance(e, CADDimension):
            sx1, sy1 = self.cad.world_to_screen(e.p1.x, e.p1.y, w, h)
            sx2, sy2 = self.cad.world_to_screen(e.p2.x, e.p2.y, w, h)
            self.canvas.create_line(
                sx1, sy1, sx2, sy2, fill=color, width=width, tags="entity", dash=(4, 2)
            )
            val = e.value()
            mx, my = (sx1 + sx2) / 2, (sy1 + sy2) / 2 - 10
            self.canvas.create_text(
                mx, my, text=f"{val:.1f} мм", fill=color, font=("Segoe UI", 9), tags="entity"
            )

        elif isinstance(e, CADPolyline):
            if len(e.points) < 2:
                return
            pts = []
            for p in e.points:
                sx, sy = self.cad.world_to_screen(p.x, p.y, w, h)
                pts.extend([sx, sy])
            if e.closed and len(pts) >= 4:
                self.canvas.create_polygon(
                    pts, outline=color, fill="", width=width, tags="entity", dash=dash
                )
            else:
                self.canvas.create_line(pts, fill=color, width=width, tags="entity", dash=dash)

        elif isinstance(e, CADText):
            sx, sy = self.cad.world_to_screen(e.x, e.y, w, h)
            anchor = {"left": "w", "center": "center", "right": "e"}.get(e.align, "w")
            self.canvas.create_text(
                sx,
                sy,
                text=e.text,
                fill=color,
                font=("Segoe UI", int(e.height * self.cad.scale)),
                anchor=anchor,
                tags="entity",
                angle=e.angle,
            )

        elif isinstance(e, CADHatch):
            if len(e.boundary) < 3:
                return
            pts = []
            for p in e.boundary:
                sx, sy = self.cad.world_to_screen(p.x, p.y, w, h)
                pts.extend([sx, sy])
            self.canvas.create_polygon(
                pts, outline=color, fill="#f0f0f0", width=1, tags="entity", dash=(2, 2)
            )

        elif isinstance(e, CADHole):
            sx, sy = self.cad.world_to_screen(e.center.x, e.center.y, w, h)
            sr = e.radius * self.cad.scale
            self.canvas.create_oval(
                sx - sr, sy - sr, sx + sr, sy + sr, outline=color, width=width, tags="entity"
            )
            self.canvas.create_line(sx - sr, sy, sx + sr, sy, fill=color, width=1, tags="entity")
            self.canvas.create_line(sx, sy - sr, sx, sy + sr, fill=color, width=1, tags="entity")
            if e.label:
                self.canvas.create_text(
                    sx, sy - sr - 5, text=e.label, fill=color, font=("Segoe UI", 8), tags="entity"
                )

    # ------------------------------------------------------------------
    # Полілінія, текст, штрихування
    # ------------------------------------------------------------------
    def _finish_polyline(self):
        if len(self.temp_points) >= 2:
            poly = CADPolyline([p.copy() for p in self.temp_points], closed=True)
            self.cad.add_entity(poly)
            self.status_label.config(text="Полілінію додано")
        self.temp_points = []
        self.drawing = False
        self.canvas.delete("preview")
        self.redraw()
        self._update_undo_label()

    def _ask_text(self, p):
        dialog = tk.Toplevel(self)
        dialog.title("Текст")
        dialog.transient(self)
        dialog.grab_set()
        tk.Label(dialog, text="Текст:", font=("Segoe UI", 10)).pack(padx=10, pady=5)
        entry = tk.Entry(dialog, width=30, font=("Segoe UI", 10))
        entry.pack(padx=10, pady=5)
        entry.focus_set()

        def ok():
            text = entry.get()
            if text:
                self.cad.add_entity(CADText(p.x, p.y, text))
                self.redraw()
                self._update_undo_label()
            dialog.destroy()

        def cancel():
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(
            btn_frame,
            text="OK",
            command=ok,
            bg=self.colors["accent"],
            fg="white",
            font=("Segoe UI", 9),
            width=8,
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Скасувати", command=cancel, font=("Segoe UI", 9), width=8).pack(
            side=tk.LEFT, padx=5
        )
        dialog.bind("<Return>", lambda e: ok())
        dialog.bind("<Escape>", lambda e: cancel())

    def _create_hatch_at(self, p):
        for e in reversed(self.cad.get_visible_entities()):
            if isinstance(e, CADPolyline | CADRectangle | CADCircle) and e.hit_test(
                p.x, p.y, tol=1
            ):
                boundary = []
                if isinstance(e, CADPolyline):
                    boundary = [pt.copy() for pt in e.points]
                    if not e.closed and len(boundary) >= 3:
                        boundary.append(boundary[0].copy())
                elif isinstance(e, CADRectangle):
                    x1, y1 = e.p1.x, e.p1.y
                    x2, y2 = e.p2.x, e.p2.y
                    boundary = [
                        CADPoint(x1, y1),
                        CADPoint(x2, y1),
                        CADPoint(x2, y2),
                        CADPoint(x1, y2),
                    ]
                elif isinstance(e, CADCircle):
                    n = 16
                    boundary = [
                        CADPoint(
                            e.center.x + e.radius * math.cos(2 * math.pi * i / n),
                            e.center.y + e.radius * math.sin(2 * math.pi * i / n),
                        )
                        for i in range(n)
                    ]
                if boundary:
                    self.cad.add_entity(CADHatch(boundary))
                    self.redraw()
                    self._update_undo_label()
                    self.status_label.config(text="Штрихування додано")
                return
        self.status_label.config(text="Не знайдено замкнутої області")

    # ------------------------------------------------------------------
    # Властивості та координати
    # ------------------------------------------------------------------
    def update_properties(self):
        sel = self.cad.get_selected()
        self.prop_text.config(state="normal")
        self.prop_text.delete("1.0", tk.END)
        if not sel:
            self.prop_text.insert(
                tk.END,
                f"Об'єктів: {len(self.cad.entities)}\n"
                f"Видимих: {len(self.cad.get_visible_entities())}\n"
                f"Загальна площа: {self.cad.get_total_area():.2f} мм²\n"
                f"Загальний периметр: {self.cad.get_total_perimeter():.2f} мм\n",
            )
        else:
            self.prop_text.insert(tk.END, f"Вибрано: {len(sel)} об'єкт(ів)\n")
            for e in sel:
                self.prop_text.insert(tk.END, f"\n{type(e).__name__} #{e.id}\n")
                self.prop_text.insert(tk.END, f"  Шар: {e.layer}\n")
                self.prop_text.insert(tk.END, f"  Колір: {e.color}\n")
                if hasattr(e, "length") and callable(e.length):
                    self.prop_text.insert(tk.END, f"  Довжина: {e.length():.2f} мм\n")
                if hasattr(e, "area") and callable(e.area) and e.area() > 0:
                    self.prop_text.insert(tk.END, f"  Площа: {e.area():.2f} мм²\n")
                if hasattr(e, "perimeter") and callable(e.perimeter) and e.perimeter() > 0:
                    self.prop_text.insert(tk.END, f"  Периметр: {e.perimeter():.2f} мм\n")
        self.prop_text.config(state="disabled")

    def _update_size_entry(self, p):
        if not self.drawing or not self.drag_start:
            return
        tool = self.current_tool
        val = ""
        if tool == "line":
            val = f"{math.hypot(p.x - self.drag_start.x, p.y - self.drag_start.y):.1f}"
        elif tool == "rectangle":
            w = abs(p.x - self.drag_start.x)
            h = abs(p.y - self.drag_start.y)
            val = f"{w:.1f}x{h:.1f}"
        elif tool == "arc":
            val = ""  # arc uses separate preview, not size entry
        elif tool in ("circle", "hole") or tool == "dimension":
            val = f"{math.hypot(p.x - self.drag_start.x, p.y - self.drag_start.y):.1f}"
        self.size_entry.config(state="normal")
        self.size_entry.delete(0, tk.END)
        self.size_entry.insert(0, val)
        self.size_entry.config(state="normal")
        # preview value: for arc take radius only (before comma)
        if "," in val:
            self._size_preview_val = float(val.split(",")[0])
        elif "x" in val:
            self._size_preview_val = float(val.split("x")[0])
        else:
            self._size_preview_val = float(val)
        self._size_preview_tool = tool

    def _clear_size_entry(self):
        self.size_entry.config(state="normal")
        self.size_entry.delete(0, tk.END)
        self.size_entry.config(state="disabled")
        self._size_preview_val = 0.0
        self._size_preview_tool = None
        self._last_drag_point = None

    def _show_size_dialog(self, entity, tool, start, end):
        """Показати діалог точного розміру біля накресленого елемента"""
        print("[DEBUG] _show_size_dialog called, tool=", tool)

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        if tool == "line":
            cx = (start.x + end.x) / 2
            cy = (start.y + end.y) / 2
            val = f"{entity.length():.1f}"
            label = "Довжина (мм):"
        elif tool == "rectangle":
            cx = (start.x + end.x) / 2
            cy = (start.y + end.y) / 2
            val = f"{entity.width():.1f}x{entity.height():.1f}"
            label = "Ш x В (мм):"
        elif tool == "arc" or tool in ("circle", "hole"):
            cx, cy = start.x, start.y
            val = f"{entity.radius:.1f}"
            label = "Радіус (мм):"
        elif tool == "dimension":
            cx = (start.x + end.x) / 2
            cy = (start.y + end.y) / 2
            val = f"{entity.value():.1f}"
            label = "Довжина (мм):"
        else:
            return

        sx, sy = self.cad.world_to_screen(cx, cy, w, h)
        rx = self.canvas.winfo_rootx() + int(sx)
        ry = self.canvas.winfo_rooty() + int(sy)

        root = self.winfo_toplevel()
        dialog = tk.Toplevel(root)
        dialog.title("Точний розмір")
        dialog.transient(root)
        dialog.resizable(False, False)
        dialog.configure(bg="#fff3cd")
        dialog.geometry(f"+{rx - 70}+{ry - 70}")

        frame = tk.Frame(dialog, bg="#fff3cd", padx=12, pady=10)
        frame.pack()

        tk.Label(
            frame, text=label, bg="#fff3cd", fg="#856404", font=("Segoe UI", 10, "bold")
        ).pack()

        entry = tk.Entry(
            frame, width=14, font=("Segoe UI", 11), justify="center", relief=tk.SOLID, bd=1
        )
        entry.insert(0, val)
        entry.pack(pady=(6, 8))
        entry.select_range(0, tk.END)

        btn_frame = tk.Frame(frame, bg="#fff3cd")
        btn_frame.pack()

        def apply():
            txt = entry.get().strip().replace(" ", "")
            if not txt:
                dialog.destroy()
                return
            try:
                self._recreate_entity(entity, tool, start, end, txt)
                dialog.destroy()
            except ValueError:
                entry.config(fg="red")
                dialog.after(500, lambda: entry.config(fg="black"))

        def cancel():
            dialog.destroy()

        tk.Button(
            btn_frame,
            text="OK  ↵",
            command=apply,
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            width=8,
        ).pack(side=tk.LEFT, padx=3)
        tk.Button(
            btn_frame, text="Скасувати  Esc", command=cancel, font=("Segoe UI", 9), width=12
        ).pack(side=tk.LEFT, padx=3)

        dialog.bind("<Return>", lambda e: apply())
        dialog.bind("<Escape>", lambda e: cancel())

        dialog.lift()
        dialog.focus_set()
        entry.focus_force()
        entry.select_range(0, tk.END)

    def _recreate_entity(self, old_entity, tool, start, end, txt):
        """Видалити старий елемент і створити новий з точним розміром"""
        # Видалити старий
        self.cad.delete_entity(old_entity)
        # Напрямок
        dx = end.x - start.x
        dy = end.y - start.y
        angle = math.atan2(dy, dx) if (dx != 0 or dy != 0) else 0

        new_entity = None
        if tool == "line":
            dist = float(txt)
            new_end = CADPoint(start.x + dist * math.cos(angle), start.y + dist * math.sin(angle))
            new_entity = CADLine(start, new_end)
            self.status_label.config(text=f"Лінію оновлено ({dist:.1f} мм)")
        elif tool == "rectangle":
            if "x" in txt.lower():
                parts = txt.lower().split("x")
                w = float(parts[0])
                h = float(parts[1])
            else:
                w = h = float(txt)
            sx = 1 if dx >= 0 else -1
            sy = 1 if dy >= 0 else -1
            new_end = CADPoint(start.x + w * sx, start.y + h * sy)
            new_entity = CADRectangle(start, new_end)
            self.status_label.config(text=f"Прямокутник оновлено ({w:.1f}x{h:.1f} мм)")
        elif tool == "circle":
            r = float(txt)
            if r > 0:
                new_entity = CADCircle(start, r)
                self.status_label.config(text=f"Коло оновлено (R={r:.1f} мм)")
        elif tool == "arc":
            r = float(txt)
            if r > 0:
                end_angle = math.degrees(angle)
                new_entity = CADArc(start, r, end_angle, end_angle + 180)
                self.status_label.config(text=f"Дугу оновлено (R={r:.1f} мм)")
        elif tool == "dimension":
            dist = float(txt)
            new_end = CADPoint(start.x + dist * math.cos(angle), start.y + dist * math.sin(angle))
            new_entity = CADDimension(start, new_end)
            self.status_label.config(text=f"Розмір оновлено ({dist:.1f} мм)")
        elif tool == "hole":
            r = float(txt)
            if r > 0:
                new_entity = CADHole(start, r)
                self.status_label.config(text=f"Отвір оновлено (R={r:.1f} мм)")

        if new_entity:
            self.cad.add_entity(new_entity)
            self.redraw()
            self._update_undo_label()

    def _finish_shape(self, p):
        """Завершити креслення поточної фігури точкою p, потім показати діалог розміру"""
        if not self.drawing or not self.drag_start:
            print(
                "[DEBUG] _finish_shape early return: drawing=",
                self.drawing,
                "drag_start=",
                self.drag_start,
            )
            return
        tool = self.current_tool
        start = self.drag_start
        entity = None
        if tool == "line":
            entity = CADLine(start, p)
            self.cad.add_entity(entity)
            self.status_label.config(text="Лінію додано — вкажіть точний розмір")
        elif tool == "rectangle":
            entity = CADRectangle(start, p)
            self.cad.add_entity(entity)
            self.status_label.config(text="Прямокутник додано — вкажіть точний розмір")
        elif tool == "circle":
            r = math.hypot(p.x - start.x, p.y - start.y)
            if r > 0:
                entity = CADCircle(start, r)
                self.cad.add_entity(entity)
                self.status_label.config(text="Коло додано — вкажіть точний розмір")
        elif tool == "arc":
            r = math.hypot(p.x - start.x, p.y - start.y)
            if r > 0:
                angle = math.degrees(math.atan2(p.y - start.y, p.x - start.x)) % 360
                sweep = min(angle, 180)
                entity = CADArc(start, r, 0, sweep)
                self.cad.add_entity(entity)
                self.status_label.config(text=f"Дугу додано ({sweep:.0f}°) — вкажіть точний розмір")
        elif tool == "dimension":
            entity = CADDimension(start, p)
            self.cad.add_entity(entity)
            self.status_label.config(text="Розмір додано — вкажіть точний розмір")
        elif tool == "hole":
            r = math.hypot(p.x - start.x, p.y - start.y)
            if r > 0:
                entity = CADHole(start, r)
                self.cad.add_entity(entity)
                self.status_label.config(text="Отвір додано — вкажіть точний розмір")
        self.drawing = False
        self.drag_start = None
        self._last_drag_point = None
        self.canvas.delete("preview")
        self.redraw()
        self._update_undo_label()
        self._clear_size_entry()
        if entity:
            print("[DEBUG] entity created, calling _show_size_dialog")
            self._show_size_dialog(entity, tool, start, p)
        else:
            print("[DEBUG] entity is None — no dialog shown")
        self._last_drag_point = None

    def on_size_entry(self, event):
        if not self.drawing or not self.drag_start:
            return
        txt = self.size_entry.get().strip().replace(" ", "")
        if not txt:
            return
        try:
            # Parse value based on tool
            tool = self.current_tool
            start = self.drag_start
            # Current angle/direction from drag
            cur_p, _ = self._get_snapped_pos(None)  # can't use this, need last mouse pos
            # Instead, use the stored preview value direction
            # We'll compute from current temp point if exists, otherwise use default direction
            # Actually, let's use the last known mouse position via last_world_pos
            if self.last_world_pos:
                cur_x, cur_y = self.last_world_pos
            else:
                cur_x, cur_y = start.x + 10, start.y

            dx = cur_x - start.x
            dy = cur_y - start.y
            angle = math.atan2(dy, dx) if (dx != 0 or dy != 0) else 0

            if tool == "line":
                dist = float(txt)
                end = CADPoint(start.x + dist * math.cos(angle), start.y + dist * math.sin(angle))
                self.cad.add_entity(CADLine(start, end))
                self.status_label.config(text=f"Лінію додано ({dist:.1f} мм)")

            elif tool == "rectangle":
                if "x" in txt.lower():
                    parts = txt.lower().split("x")
                    w = float(parts[0])
                    h = float(parts[1])
                else:
                    w = h = float(txt)
                # Preserve quadrant from drag direction
                sx = 1 if dx >= 0 else -1
                sy = 1 if dy >= 0 else -1
                end = CADPoint(start.x + w * sx, start.y + h * sy)
                self.cad.add_entity(CADRectangle(start, end))
                self.status_label.config(text=f"Прямокутник додано ({w:.1f}x{h:.1f} мм)")

            elif tool == "circle":
                r = float(txt)
                if r > 0:
                    self.cad.add_entity(CADCircle(start, r))
                    self.status_label.config(text=f"Коло додано (R={r:.1f} мм)")

            elif tool == "arc":
                r = float(txt)
                if r > 0:
                    end_angle = math.degrees(angle)
                    self.cad.add_entity(CADArc(start, r, end_angle, end_angle + 180))
                    self.status_label.config(text=f"Дугу додано (R={r:.1f} мм)")

            elif tool == "dimension":
                dist = float(txt)
                end = CADPoint(start.x + dist * math.cos(angle), start.y + dist * math.sin(angle))
                self.cad.add_entity(CADDimension(start, end))
                self.status_label.config(text=f"Розмір додано ({dist:.1f} мм)")

            elif tool == "hole":
                r = float(txt)
                if r > 0:
                    self.cad.add_entity(CADHole(start, r))
                    self.status_label.config(text=f"Отвір додано (R={r:.1f} мм)")

            self.drawing = False
            self.drag_start = None
            self.canvas.delete("preview")
            self.redraw()
            self._update_undo_label()
            self._clear_size_entry()
        except ValueError:
            self.status_label.config(text="Помилка формату розміру")

    def on_coord_entry(self, event):
        txt = self.coord_entry.get().replace(" ", "")
        if "," in txt:
            try:
                x, y = map(float, txt.split(","))
                self.last_world_pos = (x, y)
                self.coord_label.config(text=f"X: {x:.2f}  Y: {y:.2f}")
                self.status_label.config(text=f"Координати: {x}, {y}")
            except ValueError:
                self.status_label.config(text="Помилка формату координат")

    # ------------------------------------------------------------------
    # Файли
    # ------------------------------------------------------------------
    def save_drawing(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json")]
        )
        if path:
            self.cad.save_json(path)
            self.status_label.config(text=f"Збережено: {path}")

    def load_drawing(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            self.cad.load_json(path)
            self.redraw()
            self.update_properties()
            self.status_label.config(text=f"Завантажено: {path}")

    def export_svg(self):
        path = filedialog.asksaveasfilename(defaultextension=".svg", filetypes=[("SVG", "*.svg")])
        if path:
            self.cad.export_svg(path, self.canvas.winfo_width(), self.canvas.winfo_height())
            self.status_label.config(text=f"Експортовано SVG: {path}")

    def export_dxf(self):
        path = filedialog.asksaveasfilename(defaultextension=".dxf", filetypes=[("DXF", "*.dxf")])
        if path:
            self.cad.export_dxf(path)
            self.status_label.config(text=f"Експортовано DXF: {path}")

    def export_freecad(self):
        """Експорт креслення у FreeCAD .FCStd"""
        if not FREECAD_AVAILABLE:
            messagebox.showwarning(
                "FreeCAD не встановлено",
                "Для експорту у FreeCAD потрібно встановити його:\n"
                "\nLinux: sudo apt install freecad"
                "\nWindows: https://www.freecadweb.org/downloads.php",
            )
            return

        if not self.cad.entities:
            messagebox.showinfo("Порожнє креслення", "Немає об'єктів для експорту")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".FCStd",
            filetypes=[("FreeCAD", "*.FCStd"), ("DXF", "*.dxf")],
            title="Експорт у FreeCAD",
        )
        if not path:
            return

        try:
            exporter = FreeCADExporter()
            if path.lower().endswith(".dxf"):
                exporter.export_to_dxf(self.cad.entities, path)
            else:
                exporter.export_entities(self.cad.entities, path)
            exporter.close()
            self.status_label.config(text=f"✅ Експортовано у FreeCAD: {path}")

            # Пропонуємо відкрити у FreeCAD
            if messagebox.askyesno("Відкрити FreeCAD?", "Відкрити файл у FreeCAD?"):
                self._open_in_freecad(path)

        except Exception as e:
            messagebox.showerror("Помилка експорту", f"Не вдалося експортувати:\n{str(e)}")
            self.status_label.config(text=f"❌ Помилка експорту: {e}")

    def _open_in_freecad(self, filepath):
        """Відкрити файл у зовнішньому FreeCAD"""
        import platform
        import subprocess

        system = platform.system()
        try:
            if system == "Windows":
                subprocess.Popen(["freecad.exe", filepath], shell=True)
            else:
                subprocess.Popen(["freecad", filepath])
            self.status_label.config(text="🖥️ FreeCAD запущено")
        except FileNotFoundError:
            messagebox.showwarning(
                "FreeCAD не знайдено",
                "Не вдалося знайти команду 'freecad'.\n" "Відкрийте файл вручну.",
            )

    def clear_drawing(self):
        if messagebox.askyesno("Очистити", "Ви впевнені, що хочете очистити креслення?"):
            self.cad.clear()
            self.redraw()
            self.update_properties()
            self._update_undo_label()
            self.status_label.config(text="Креслення очищено")


# ===================================================================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("CAD Редактор 2.0")
    root.geometry("1200x800")
    root.configure(bg="#f0f0f0")
    app = CADEditorFrame(root, bg="#f0f0f0")
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
