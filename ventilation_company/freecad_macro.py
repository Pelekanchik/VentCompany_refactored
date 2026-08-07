"""Макрос FreeCAD для створення 3D-моделей вентиляційних виробів.

Викликається через python.exe з папки FreeCAD:
    python.exe freecad_macro.py input.json output.FCStd fcstd

Аргументи (позиційні):
    1. Шлях до JSON з виробами
    2. Шлях для збереження результату
    3. Формат: fcstd / step / stl
"""

import json
import math
import sys

import FreeCAD
import Part


def make_rect_duct(width, height, length, thickness=0.7):
    """Прямокутний повітропровід (порожнистий)."""
    w, h, ln = width / 2, height / 2, length
    t = thickness
    outer = Part.makeBox(width, height, ln)
    outer.translate(FreeCAD.Vector(-w, -h, 0))
    if t > 0.01:
        iw, ih = width - 2 * t, height - 2 * t
        if iw > 0 and ih > 0:
            inner = Part.makeBox(iw, ih, ln + 0.1)
            inner.translate(FreeCAD.Vector(-iw / 2, -ih / 2, -0.05))
            return outer.cut(inner)
    return outer


def make_round_duct(diameter, length, thickness=0.7):
    """Круглий повітропровід (труба)."""
    r = diameter / 2
    t = thickness
    outer = Part.makeCylinder(r, length)
    if t > 0.01 and r > t:
        inner = Part.makeCylinder(r - t, length + 0.1)
        inner.translate(FreeCAD.Vector(0, 0, -0.05))
        return outer.cut(inner)
    return outer


def make_rect_flange(width, height, border=30, thickness=3, bolt_d=10):
    """Прямокутний фланець з отворами."""
    w = width + 2 * border
    h = height + 2 * border
    t = thickness
    plate = Part.makeBox(w, h, t)
    plate.translate(FreeCAD.Vector(-w / 2, -h / 2, 0))
    hole = Part.makeBox(width, height, t + 0.1)
    hole.translate(FreeCAD.Vector(-width / 2, -height / 2, -0.05))
    shape = plate.cut(hole)
    bolt_r = bolt_d / 2
    bx = max(1, int((w - 40) / 100) + 1)
    by = max(1, int((h - 40) / 100) + 1)
    for i in range(bx):
        for j in range(by):
            x = -w / 2 + 20 + i * 100
            y = -h / 2 + 20 + j * 100
            bh = Part.makeCylinder(bolt_r, t + 0.1)
            bh.translate(FreeCAD.Vector(x, y, -0.05))
            shape = shape.cut(bh)
    return shape


def make_round_flange(diameter, width=30, thickness=3, bolt_count=8, bolt_d=10):
    """Круглий фланець."""
    r = (diameter / 2) + width
    t = thickness
    outer = Part.makeCylinder(r, t)
    inner = Part.makeCylinder(diameter / 2, t + 0.1)
    inner.translate(FreeCAD.Vector(0, 0, -0.05))
    shape = outer.cut(inner)
    bolt_r = bolt_d / 2
    bolt_circle_r = (diameter / 2) + (width / 2)
    for i in range(bolt_count):
        angle = 2 * math.pi * i / bolt_count
        x = bolt_circle_r * math.cos(angle)
        y = bolt_circle_r * math.sin(angle)
        bh = Part.makeCylinder(bolt_r, t + 0.1)
        bh.translate(FreeCAD.Vector(x, y, -0.05))
        shape = shape.cut(bh)
    return shape


# ── ТРІЙНИКИ З OFFSET ───────────────────────────────────────────


def make_rect_tee(w, h, length, bw, bh, bl, offset, thickness=0.7):
    """Прямокутний трійник.

    offset — відстань від початку основного каналу (Z=0) до центру відгалуження.
    Відгалуження йде вгору (вздовж +Y).
    """
    # Основний канал вздовж Z
    main = make_rect_duct(w, h, length, thickness)

    # Відгалуження вздовж Y (вгору)
    branch = Part.makeBox(bw, bl, bh)
    branch.translate(FreeCAD.Vector(-bw / 2, 0, -bh / 2))
    if thickness > 0.01:
        ibw, ibh = bw - 2 * thickness, bh - 2 * thickness
        if ibw > 0 and ibh > 0:
            inner = Part.makeBox(ibw, bl + 0.1, ibh)
            inner.translate(FreeCAD.Vector(-ibw / 2, -0.05, -ibh / 2))
            branch = branch.cut(inner)

    # Зміщуємо відгалуження: центр по Z = offset, по Y = верх основного каналу
    branch.translate(FreeCAD.Vector(0, h / 2, offset))

    return main.fuse(branch)


def make_round_tee(d, length, bd, bl, offset, thickness=0.7):
    """Круглий трійник.

    offset — відстань від початку основної труби (Z=0) до центру відгалуження.
    """
    main = make_round_duct(d, length, thickness)

    # Відгалуження — циліндр вздовж Y
    branch = Part.makeCylinder(bd / 2, bl)
    branch.translate(FreeCAD.Vector(0, 0, -bd / 2))
    if thickness > 0.01 and bd / 2 > thickness:
        inner = Part.makeCylinder(bd / 2 - thickness, bl + 0.1)
        inner.translate(FreeCAD.Vector(0, -0.05, -bd / 2))
        branch = branch.cut(inner)

    # Повертаємо на 90° навколо X (Y стане Z, Z стане -Y)
    # Потім зміщуємо: центр по Z = offset, по Y = верх труби
    branch.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), 90)
    branch.translate(FreeCAD.Vector(0, d / 2, offset))

    return main.fuse(branch)


# ── ПЕРЕХОДИ ────────────────────────────────────────────────────


def make_rect_transition(w1, h1, w2, h2, length, thickness=0.7):
    """Прямокутний перехід."""

    def rect_wire(w, h, z):
        pts = [
            FreeCAD.Vector(-w / 2, -h / 2, z),
            FreeCAD.Vector(w / 2, -h / 2, z),
            FreeCAD.Vector(w / 2, h / 2, z),
            FreeCAD.Vector(-w / 2, h / 2, z),
            FreeCAD.Vector(-w / 2, -h / 2, z),
        ]
        return Part.makePolygon(pts)

    p1 = rect_wire(w1, h1, 0)
    p2 = rect_wire(w2, h2, length)
    shape = Part.makeLoft([p1, p2], True)
    if thickness > 0.01:
        p1_in = rect_wire(w1 - 2 * thickness, h1 - 2 * thickness, 0)
        p2_in = rect_wire(w2 - 2 * thickness, h2 - 2 * thickness, length)
        inner = Part.makeLoft([p1_in, p2_in], True)
        shape = shape.cut(inner)
    return shape


def make_round_transition(d1, d2, length, thickness=0.7):
    """Круглий перехід."""
    r1, r2 = d1 / 2, d2 / 2
    c1 = Part.makeCircle(r1, FreeCAD.Vector(0, 0, 0))
    c2 = Part.makeCircle(r2, FreeCAD.Vector(0, 0, length))
    w1 = Part.Wire([c1])
    w2 = Part.Wire([c2])
    shape = Part.makeLoft([w1, w2], True)
    if thickness > 0.01:
        c1_in = Part.makeCircle(r1 - thickness, FreeCAD.Vector(0, 0, 0))
        c2_in = Part.makeCircle(r2 - thickness, FreeCAD.Vector(0, 0, length))
        w1_in = Part.Wire([c1_in])
        w2_in = Part.Wire([c2_in])
        inner = Part.makeLoft([w1_in, w2_in], True)
        shape = shape.cut(inner)
    return shape


# ── ВІДВОДИ ─────────────────────────────────────────────────────


def make_rect_elbow(w, h, angle=90, radius=150, segments=3, thickness=0.7):
    """Прямокутне коліно."""
    angle_rad = math.radians(angle)
    seg_angle = angle_rad / segments
    r = radius

    def rect_wire(wi, hi, z):
        pts = [
            FreeCAD.Vector(-wi / 2, -hi / 2, z),
            FreeCAD.Vector(wi / 2, -hi / 2, z),
            FreeCAD.Vector(wi / 2, hi / 2, z),
            FreeCAD.Vector(-wi / 2, hi / 2, z),
            FreeCAD.Vector(-wi / 2, -hi / 2, z),
        ]
        return Part.makePolygon(pts)

    wires = []
    for i in range(segments + 1):
        a = i * seg_angle
        cx = r * math.sin(a)
        cz = r * (1 - math.cos(a))
        wire = rect_wire(w, h, 0)
        wire.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0), math.degrees(a))
        wire.translate(FreeCAD.Vector(cx, 0, cz))
        wires.append(wire)

    shape = Part.makeLoft(wires, True)
    if thickness > 0.01:
        wires_in = []
        for i in range(segments + 1):
            a = i * seg_angle
            cx = r * math.sin(a)
            cz = r * (1 - math.cos(a))
            wire = rect_wire(w - 2 * thickness, h - 2 * thickness, 0)
            wire.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0), math.degrees(a))
            wire.translate(FreeCAD.Vector(cx, 0, cz))
            wires_in.append(wire)
        inner = Part.makeLoft(wires_in, True)
        shape = shape.cut(inner)
    return shape


def make_round_elbow(d, angle=90, radius=150, segments=3, thickness=0.7):
    """Кругле коліно."""
    angle_rad = math.radians(angle)
    seg_angle = angle_rad / segments
    r = radius
    r_pipe = d / 2

    wires = []
    for i in range(segments + 1):
        a = i * seg_angle
        cx = r * math.sin(a)
        cz = r * (1 - math.cos(a))
        c = Part.makeCircle(r_pipe, FreeCAD.Vector(cx, 0, cz))
        wire = Part.Wire([c])
        wire.rotate(FreeCAD.Vector(cx, 0, cz), FreeCAD.Vector(0, 1, 0), math.degrees(a))
        wires.append(wire)

    shape = Part.makeLoft(wires, True)
    if thickness > 0.01:
        wires_in = []
        for i in range(segments + 1):
            a = i * seg_angle
            cx = r * math.sin(a)
            cz = r * (1 - math.cos(a))
            c = Part.makeCircle(r_pipe - thickness, FreeCAD.Vector(cx, 0, cz))
            wire = Part.Wire([c])
            wire.rotate(FreeCAD.Vector(cx, 0, cz), FreeCAD.Vector(0, 1, 0), math.degrees(a))
            wires_in.append(wire)
        inner = Part.makeLoft(wires_in, True)
        shape = shape.cut(inner)
    return shape


# ── ЗАГЛУШКИ ────────────────────────────────────────────────────


def make_rect_cap(w, h, depth=30, thickness=0.7):
    """Прямокутна заглушка."""
    bottom = Part.makeBox(w, h, thickness)
    bottom.translate(FreeCAD.Vector(-w / 2, -h / 2, 0))
    t = thickness
    side_n = Part.makeBox(w, t, depth)
    side_n.translate(FreeCAD.Vector(-w / 2, -h / 2 - t, thickness))
    side_s = Part.makeBox(w, t, depth)
    side_s.translate(FreeCAD.Vector(-w / 2, h / 2, thickness))
    side_w = Part.makeBox(t, h, depth)
    side_w.translate(FreeCAD.Vector(-w / 2 - t, -h / 2, thickness))
    side_e = Part.makeBox(t, h, depth)
    side_e.translate(FreeCAD.Vector(w / 2, -h / 2, thickness))
    return bottom.fuse(side_n).fuse(side_s).fuse(side_w).fuse(side_e)


def make_round_cap(d, depth=30, thickness=0.7):
    """Кругла заглушка."""
    r = d / 2
    bottom = Part.makeCylinder(r, thickness)
    side = Part.makeCylinder(r, depth)
    side.translate(FreeCAD.Vector(0, 0, thickness))
    if r > thickness:
        inner = Part.makeCylinder(r - thickness, depth + 0.1)
        inner.translate(FreeCAD.Vector(0, 0, thickness - 0.05))
        side = side.cut(inner)
    return bottom.fuse(side)


# ── ГНУЧКА ВСТАВКА ──────────────────────────────────────────────


def make_flexible_connector(w, h, length, thickness=0.7):
    """Гнучка вставка — спрощено як прямокутний канал."""
    return make_rect_duct(w, h, length, thickness)


# ── БУДІВНИК ВИРОБІВ ────────────────────────────────────────────


def build_product(data, doc, offset_x=0):
    """Створити 3D-модель виробу."""
    ptype = data.get("type", "")
    name = data.get("name", "Product")
    w = data.get("width", 0)
    h = data.get("height", 0)
    length = data.get("length", 0)
    thickness = data.get("thickness", 0.7)

    if "повітропровід прямокутний" in ptype:
        shape = make_rect_duct(w, h, length, thickness)
    elif "повітропровід круглий" in ptype:
        shape = make_round_duct(h, length, thickness)
    elif "фланець прямокутний" in ptype:
        border = data.get("flange_border", 30)
        bolt_d = data.get("bolt_diameter", 10)
        shape = make_rect_flange(w, h, border, 3, bolt_d)
    elif "фланець круглий" in ptype:
        width = data.get("flange_width", 30)
        bolt_count = data.get("bolt_count", 8)
        bolt_d = data.get("bolt_diameter", 10)
        shape = make_round_flange(h, width, 3, bolt_count, bolt_d)
    elif "трійник прямокутний" in ptype:
        bw = data.get("branch_width", w * 0.5)
        bh = data.get("branch_height", h * 0.5)
        bl = data.get("branch_length", length * 0.5)
        offset = data.get("branch_offset", length * 0.5)
        shape = make_rect_tee(w, h, length, bw, bh, bl, offset, thickness)
    elif "трійник круглий" in ptype:
        bd = data.get("branch_diameter", h * 0.5)
        bl = data.get("branch_length", length * 0.5)
        offset = data.get("branch_offset", length * 0.5)
        shape = make_round_tee(h, length, bd, bl, offset, thickness)
    elif "перехід прямокутний" in ptype:
        ew = data.get("end_width", w)
        eh = data.get("end_height", h)
        shape = make_rect_transition(w, h, ew, eh, length, thickness)
    elif "перехід круглий" in ptype:
        ed = data.get("end_diameter", h)
        shape = make_round_transition(h, ed, length, thickness)
    elif "відвід прямокутний" in ptype:
        angle = data.get("angle", 90)
        radius = data.get("radius", 150)
        segments = data.get("segments", 3)
        shape = make_rect_elbow(w, h, angle, radius, segments, thickness)
    elif "відвід круглий" in ptype:
        angle = data.get("angle", 90)
        radius = data.get("radius", 150)
        segments = data.get("segments", 3)
        shape = make_round_elbow(h, angle, radius, segments, thickness)
    elif "заглушка прямокутна" in ptype:
        depth = data.get("flange_border", 25)
        shape = make_rect_cap(w, h, depth, thickness)
    elif "заглушка кругла" in ptype:
        depth = data.get("depth", 30)
        shape = make_round_cap(h, depth, thickness)
    elif "гнучка вставка" in ptype:
        shape = make_flexible_connector(w, h, length, thickness)
    else:
        shape = make_rect_duct(w, h, length, thickness)

    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    obj.Placement.Base.x = offset_x
    return obj


def main():
    if len(sys.argv) < 4:
        print("Usage: freecad_macro.py <input.json> <output.file> <format>", file=sys.stderr)
        sys.exit(1)

    json_path = sys.argv[1]
    output_path = sys.argv[2]
    fmt = sys.argv[3].lower()

    with open(json_path, encoding="utf-8") as f:
        products = json.load(f)

    doc = FreeCAD.newDocument("VentProject")

    for i, prod in enumerate(products):
        build_product(prod, doc, offset_x=i * 500)

    doc.recompute()

    if fmt == "fcstd":
        doc.saveAs(output_path)
    elif fmt == "step":
        import Import

        Import.export(doc.Objects, output_path)
    elif fmt == "stl":
        import Mesh

        for obj in doc.Objects:
            if hasattr(obj, "Shape"):
                mesh = Mesh.Mesh(obj.Shape.tessellate(0.1))
                mesh.write(output_path)
                break

    FreeCAD.closeDocument(doc.Name)
    print(f"OK:{output_path}")


if __name__ == "__main__":
    main()
