"""
Модуль компонентів вентиляційної системи
"""

from ventilation_company.config import COMPONENTS, MATERIALS, WORKS


class ComponentCatalog:
    @staticmethod
    def get_materials():
        return MATERIALS

    @staticmethod
    def get_components():
        return COMPONENTS

    @staticmethod
    def get_works():
        return WORKS

    @staticmethod
    def get_material_price(material_name):
        mat = MATERIALS.get(material_name)
        return mat["ціна_за_м2"] if mat else 0

    @staticmethod
    def get_component_price(component_name):
        comp = COMPONENTS.get(component_name)
        return comp["ціна"] if comp else 0

    @staticmethod
    def get_work_price(work_name):
        work = WORKS.get(work_name)
        if work:
            return work.get("ціна_за_м2", work.get("ціна_за_шт", work.get("ціна_за_систему", 0)))
        return 0

    @staticmethod
    def search_materials(query):
        results = {}
        for name, data in MATERIALS.items():
            if query.lower() in name.lower():
                results[name] = data
        return results

    @staticmethod
    def search_components(query):
        results = {}
        for name, data in COMPONENTS.items():
            if query.lower() in name.lower():
                results[name] = data
        return results

    @staticmethod
    def print_catalog():
        print("=" * 60)
        print("KATALOH MATERIALIV".center(60))
        print("=" * 60)
        for name, data in MATERIALS.items():
            print(f"  * {name}: {data['ціна_за_м2']} hrn/{data['одиниця']}")
        print()
        print("=" * 60)
        print("KATALOH KOMPLEKTUUCHYKH".center(60))
        print("=" * 60)
        for name, data in COMPONENTS.items():
            print(f"  * {name}: {data['ціна']} hrn/{data['одиниця']}")
        print()
        print("=" * 60)
        print("KATALOH ROBIT".center(60))
        print("=" * 60)
        for name, data in WORKS.items():
            price = data.get("ціна_за_м2", data.get("ціна_за_шт", data.get("ціна_за_систему", 0)))
            print(f"  * {name}: {price} hrn/{data['одиниця']}")


class DuctCalculator:
    @staticmethod
    def calculate_rectangular_duct(width_mm, height_mm, length_m, material="оцинкована_сталь_0.7"):

        width_m = width_mm / 1000
        height_m = height_mm / 1000
        perimeter = 2 * (width_m + height_m)
        area = perimeter * length_m
        material_price = ComponentCatalog.get_material_price(material)
        material_cost = area * material_price
        work_price = ComponentCatalog.get_work_price("виготовлення_повітропроводу")
        work_cost = area * work_price
        install_price = ComponentCatalog.get_work_price("монтаж_повітропроводу")
        install_cost = area * install_price
        return {
            "type": "priamokutnyj",
            "width_mm": width_mm,
            "height_mm": height_mm,
            "length_m": length_m,
            "area_m2": round(area, 2),
            "material": material,
            "material_cost": round(material_cost, 2),
            "manufacturing_cost": round(work_cost, 2),
            "installation_cost": round(install_cost, 2),
            "total_cost": round(material_cost + work_cost + install_cost, 2),
        }

    @staticmethod
    def calculate_round_duct(diameter_mm, length_m, material="оцинкована_сталь_0.7"):
        import math

        diameter_m = diameter_mm / 1000
        area = math.pi * diameter_m * length_m
        material_price = ComponentCatalog.get_material_price(material)
        material_cost = area * material_price
        work_price = ComponentCatalog.get_work_price("виготовлення_повітропроводу")
        work_cost = area * work_price
        install_price = ComponentCatalog.get_work_price("монтаж_повітропроводу")
        install_cost = area * install_price
        return {
            "type": "kruhlyj",
            "diameter_mm": diameter_mm,
            "length_m": length_m,
            "area_m2": round(area, 2),
            "material": material,
            "material_cost": round(material_cost, 2),
            "manufacturing_cost": round(work_cost, 2),
            "installation_cost": round(install_cost, 2),
            "total_cost": round(material_cost + work_cost + install_cost, 2),
        }

    @staticmethod
    def calculate_air_velocity(air_flow_m3h, diameter_mm):
        import math

        diameter_m = diameter_mm / 1000
        area = math.pi * (diameter_m / 2) ** 2
        velocity = (air_flow_m3h / 3600) / area
        return round(velocity, 2)

    @staticmethod
    def calculate_air_velocity_rect(air_flow_m3h, width_mm, height_mm):
        width_m = width_mm / 1000
        height_m = height_mm / 1000
        area = width_m * height_m
        velocity = (air_flow_m3h / 3600) / area
        return round(velocity, 2)

    @staticmethod
    def recommend_duct_size(air_flow_m3h, max_velocity_ms=8, shape="round"):
        import math

        flow_m3s = air_flow_m3h / 3600
        required_area = flow_m3s / max_velocity_ms
        if shape == "round":
            diameter = math.sqrt((4 * required_area) / math.pi) * 1000
            standard_sizes = [100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000]
            recommended = min([s for s in standard_sizes if s >= diameter], default=1000)
            return {"shape": "kruhlyj", "diameter_mm": recommended}
        else:
            side = math.sqrt(required_area) * 1000
            standard_sizes = [100, 150, 200, 250, 300, 400, 500]
            w = min([s for s in standard_sizes if s >= side], default=500)
            h = min([s for s in standard_sizes if s >= side], default=500)
            return {"shape": "priamokutnyj", "width_mm": w, "height_mm": h}
