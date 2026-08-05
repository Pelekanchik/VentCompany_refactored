"""
Репозиторії бази даних VentCompany
"""
from ventilation_company.database.repositories.product_repo import ProductRepo
from ventilation_company.database.repositories.material_repo import MaterialRepo
from ventilation_company.database.repositories.calc_repo import CalcRepo
from ventilation_company.database.repositories.overhead_repo import OverheadRepo
from ventilation_company.database.repositories.template_repo import TemplateRepo
from ventilation_company.database.repositories.settings_repo import SettingsRepo

__all__ = [
    "ProductRepo",
    "MaterialRepo",
    "CalcRepo",
    "OverheadRepo",
    "TemplateRepo",
    "SettingsRepo",
]
