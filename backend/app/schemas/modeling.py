from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.modeling import ScenarioType, Granularity, LineItemType


# --- Scenario ---
class ScenarioCreate(BaseModel):
    name: str
    scenario_type: ScenarioType


class ScenarioOut(BaseModel):
    id: int
    model_id: int
    name: str
    scenario_type: ScenarioType
    created_at: datetime

    class Config:
        from_attributes = True


# --- TimePeriod ---
class TimePeriodCreate(BaseModel):
    label: str
    start_date: datetime
    end_date: datetime
    granularity: Granularity = Granularity.month
    sort_order: int


class TimePeriodOut(BaseModel):
    id: int
    model_id: int
    label: str
    start_date: datetime
    end_date: datetime
    granularity: Granularity
    sort_order: int

    class Config:
        from_attributes = True


# --- LineItem ---
class LineItemCreate(BaseModel):
    name: str
    section: Optional[str] = None
    item_type: LineItemType = LineItemType.input
    formula: Optional[str] = None
    account_id: Optional[int] = None
    sort_order: int = 0


class LineItemUpdate(BaseModel):
    name: Optional[str] = None
    section: Optional[str] = None
    item_type: Optional[LineItemType] = None
    formula: Optional[str] = None
    account_id: Optional[int] = None
    sort_order: Optional[int] = None


class LineItemOut(BaseModel):
    id: int
    model_id: int
    name: str
    section: Optional[str]
    item_type: LineItemType
    formula: Optional[str]
    account_id: Optional[int]
    sort_order: int

    class Config:
        from_attributes = True


# --- Model ---
class ModelCreate(BaseModel):
    name: str
    description: Optional[str] = None
    organisation_id: int


class ModelOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    organisation_id: int
    created_at: datetime
    scenarios: list[ScenarioOut] = []

    class Config:
        from_attributes = True


# --- CellValue ---
class CellValueUpsert(BaseModel):
    line_item_id: int
    scenario_id: int
    time_period_id: int
    value: float


class CellValueOverrideClear(BaseModel):
    line_item_id: int
    scenario_id: int
    time_period_id: int


# --- Grid ---
class GridCell(BaseModel):
    line_item_id: int
    time_period_id: int
    scenario_id: int
    value: Optional[float]
    is_formula: bool
    is_override: bool
    formula_text: Optional[str]
    error_message: Optional[str]


class GridResponse(BaseModel):
    model_id: int
    scenario_id: int
    time_periods: list[TimePeriodOut]
    line_items: list[LineItemOut]
    cells: list[GridCell]
