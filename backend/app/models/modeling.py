from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    Enum, Numeric, Boolean, UniqueConstraint
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ScenarioType(str, enum.Enum):
    actual = "actual"
    budget = "budget"
    forecast = "forecast"


class Granularity(str, enum.Enum):
    month = "month"
    quarter = "quarter"
    year = "year"


class LineItemType(str, enum.Enum):
    input = "input"
    formula = "formula"
    header = "header"


class FinancialModel(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    organisation_id = Column(Integer, ForeignKey("organisations.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    organisation = relationship("Organisation", back_populates="models")
    scenarios = relationship("Scenario", back_populates="model", cascade="all, delete-orphan")
    time_periods = relationship("TimePeriod", back_populates="model", order_by="TimePeriod.sort_order", cascade="all, delete-orphan")
    line_items = relationship("LineItem", back_populates="model", order_by="LineItem.sort_order", cascade="all, delete-orphan")


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    name = Column(String, nullable=False)
    scenario_type = Column(Enum(ScenarioType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    model = relationship("FinancialModel", back_populates="scenarios")
    cell_values = relationship("CellValue", back_populates="scenario", cascade="all, delete-orphan")


class TimePeriod(Base):
    __tablename__ = "time_periods"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    label = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    granularity = Column(Enum(Granularity), nullable=False, default=Granularity.month)
    sort_order = Column(Integer, nullable=False)

    model = relationship("FinancialModel", back_populates="time_periods")
    cell_values = relationship("CellValue", back_populates="time_period", cascade="all, delete-orphan")


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    name = Column(String, nullable=False)
    section = Column(String)
    item_type = Column(Enum(LineItemType), nullable=False, default=LineItemType.input)
    formula = Column(Text)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    model = relationship("FinancialModel", back_populates="line_items")
    cell_values = relationship("CellValue", back_populates="line_item", cascade="all, delete-orphan")


class CellValue(Base):
    __tablename__ = "cell_values"

    id = Column(Integer, primary_key=True, index=True)
    line_item_id = Column(Integer, ForeignKey("line_items.id"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    time_period_id = Column(Integer, ForeignKey("time_periods.id"), nullable=False)
    value = Column(Numeric(18, 4))
    error_message = Column(Text)
    is_override = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    line_item = relationship("LineItem", back_populates="cell_values")
    scenario = relationship("Scenario", back_populates="cell_values")
    time_period = relationship("TimePeriod", back_populates="cell_values")

    __table_args__ = (
        UniqueConstraint("line_item_id", "scenario_id", "time_period_id", name="uq_cell"),
    )
