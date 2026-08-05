"""ORM-моделі для продуктів/виробів."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ventilation_company.database.base import Base

if TYPE_CHECKING:
    pass


class ProductType(Base):
    __tablename__ = "product_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    icon: Mapped[str | None] = mapped_column(String, nullable=True)


class ProductSubtype(Base):
    __tablename__ = "product_subtypes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type_id: Mapped[int] = mapped_column(ForeignKey("product_types.id"))
    code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)


class SizeRange(Base):
    __tablename__ = "size_ranges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subtype_id: Mapped[int] = mapped_column(ForeignKey("product_subtypes.id"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    min_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_size: Mapped[float | None] = mapped_column(Float, nullable=True)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    product_type: Mapped[str | None] = mapped_column(String, nullable=True)
    subtype: Mapped[str | None] = mapped_column(String, nullable=True)
    size_range: Mapped[str | None] = mapped_column(String, nullable=True)
    price: Mapped[float] = mapped_column(Float, default=0)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
