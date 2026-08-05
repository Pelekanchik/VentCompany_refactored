"""ORM-репозиторії бази даних."""

from ventilation_company.database.repositories.calc_repo import CalculationRepository
from ventilation_company.database.repositories.material_repo import MaterialRepository
from ventilation_company.database.repositories.overhead_repo import OverheadRepository
from ventilation_company.database.repositories.product_repo import ProductRepository
from ventilation_company.database.repositories.settings_repo import SettingsRepository

__all__ = [
    "CalculationRepository",
    "MaterialRepository",
    "OverheadRepository",
    "ProductRepository",
    "SettingsRepository",
]
