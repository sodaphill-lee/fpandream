from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.modeling import FinancialModel, Scenario, TimePeriod, LineItem, CellValue, LineItemType
from app.schemas.modeling import (
    ModelCreate, ModelOut,
    ScenarioCreate, ScenarioOut,
    TimePeriodCreate, TimePeriodOut,
    LineItemCreate, LineItemOut, LineItemUpdate,
    CellValueUpsert, CellValueOverrideClear,
    GridResponse, GridCell,
)
from app.services.formula_engine import Evaluator

router = APIRouter(prefix="/api/models", tags=["models"])


# --- Models ---

@router.post("/", response_model=ModelOut)
def create_model(payload: ModelCreate, db: Session = Depends(get_db)):
    model = FinancialModel(**payload.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.get("/", response_model=list[ModelOut])
def list_models(organisation_id: int, db: Session = Depends(get_db)):
    return db.query(FinancialModel).filter_by(organisation_id=organisation_id).all()


@router.get("/{model_id}", response_model=ModelOut)
def get_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(FinancialModel).filter_by(id=model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.delete("/{model_id}", status_code=204)
def delete_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(FinancialModel).filter_by(id=model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    db.delete(model)
    db.commit()


# --- Scenarios ---

@router.post("/{model_id}/scenarios/", response_model=ScenarioOut)
def create_scenario(model_id: int, payload: ScenarioCreate, db: Session = Depends(get_db)):
    scenario = Scenario(model_id=model_id, **payload.model_dump())
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.get("/{model_id}/scenarios/", response_model=list[ScenarioOut])
def list_scenarios(model_id: int, db: Session = Depends(get_db)):
    return db.query(Scenario).filter_by(model_id=model_id).all()


@router.delete("/{model_id}/scenarios/{scenario_id}", status_code=204)
def delete_scenario(model_id: int, scenario_id: int, db: Session = Depends(get_db)):
    scenario = db.query(Scenario).filter_by(id=scenario_id, model_id=model_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    db.delete(scenario)
    db.commit()


# --- Time Periods ---

@router.post("/{model_id}/time_periods/", response_model=TimePeriodOut)
def create_time_period(model_id: int, payload: TimePeriodCreate, db: Session = Depends(get_db)):
    period = TimePeriod(model_id=model_id, **payload.model_dump())
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


@router.get("/{model_id}/time_periods/", response_model=list[TimePeriodOut])
def list_time_periods(model_id: int, db: Session = Depends(get_db)):
    return db.query(TimePeriod).filter_by(model_id=model_id).order_by(TimePeriod.sort_order).all()


@router.delete("/{model_id}/time_periods/{period_id}", status_code=204)
def delete_time_period(model_id: int, period_id: int, db: Session = Depends(get_db)):
    period = db.query(TimePeriod).filter_by(id=period_id, model_id=model_id).first()
    if not period:
        raise HTTPException(status_code=404, detail="Time period not found")
    db.delete(period)
    db.commit()


# --- Line Items ---

@router.post("/{model_id}/line_items/", response_model=LineItemOut)
def create_line_item(model_id: int, payload: LineItemCreate, db: Session = Depends(get_db)):
    li = LineItem(model_id=model_id, **payload.model_dump())
    db.add(li)
    db.commit()
    db.refresh(li)
    return li


@router.get("/{model_id}/line_items/", response_model=list[LineItemOut])
def list_line_items(model_id: int, db: Session = Depends(get_db)):
    return db.query(LineItem).filter_by(model_id=model_id).order_by(LineItem.sort_order).all()


@router.patch("/{model_id}/line_items/{item_id}", response_model=LineItemOut)
def update_line_item(model_id: int, item_id: int, payload: LineItemUpdate, db: Session = Depends(get_db)):
    li = db.query(LineItem).filter_by(id=item_id, model_id=model_id).first()
    if not li:
        raise HTTPException(status_code=404, detail="Line item not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(li, k, v)
    db.commit()
    db.refresh(li)
    return li


@router.delete("/{model_id}/line_items/{item_id}", status_code=204)
def delete_line_item(model_id: int, item_id: int, db: Session = Depends(get_db)):
    li = db.query(LineItem).filter_by(id=item_id, model_id=model_id).first()
    if not li:
        raise HTTPException(status_code=404, detail="Line item not found")
    db.delete(li)
    db.commit()


# --- Cell Values (inline edits) ---

@router.patch("/{model_id}/cells/", response_model=None)
def upsert_cell(model_id: int, payload: CellValueUpsert, db: Session = Depends(get_db)):
    cv = db.query(CellValue).filter_by(
        line_item_id=payload.line_item_id,
        scenario_id=payload.scenario_id,
        time_period_id=payload.time_period_id,
    ).first()
    if cv:
        cv.value = payload.value
        cv.is_override = True
    else:
        cv = CellValue(
            line_item_id=payload.line_item_id,
            scenario_id=payload.scenario_id,
            time_period_id=payload.time_period_id,
            value=payload.value,
            is_override=True,
        )
        db.add(cv)
    db.commit()
    return {"ok": True}


@router.delete("/{model_id}/cells/override", response_model=None)
def clear_override(model_id: int, payload: CellValueOverrideClear, db: Session = Depends(get_db)):
    cv = db.query(CellValue).filter_by(
        line_item_id=payload.line_item_id,
        scenario_id=payload.scenario_id,
        time_period_id=payload.time_period_id,
    ).first()
    if cv:
        cv.is_override = False
        db.commit()
    return {"ok": True}


# --- Calculate & Grid ---

def _build_grid_response(
    model_id: int,
    scenario_id: int,
    db: Session,
) -> GridResponse:
    line_items = db.query(LineItem).filter_by(model_id=model_id).order_by(LineItem.sort_order).all()
    time_periods = db.query(TimePeriod).filter_by(model_id=model_id).order_by(TimePeriod.sort_order).all()
    li_ids = {li.id for li in line_items}
    cell_values = db.query(CellValue).filter_by(scenario_id=scenario_id).filter(
        CellValue.line_item_id.in_(li_ids)
    ).all()

    li_map = {li.id: li for li in line_items}
    cells = [
        GridCell(
            line_item_id=cv.line_item_id,
            time_period_id=cv.time_period_id,
            scenario_id=cv.scenario_id,
            value=float(cv.value) if cv.value is not None else None,
            is_formula=li_map[cv.line_item_id].item_type == LineItemType.formula if cv.line_item_id in li_map else False,
            is_override=cv.is_override,
            formula_text=li_map[cv.line_item_id].formula if cv.line_item_id in li_map else None,
            error_message=cv.error_message,
        )
        for cv in cell_values
        if cv.line_item_id in li_map
    ]

    return GridResponse(
        model_id=model_id,
        scenario_id=scenario_id,
        time_periods=[TimePeriodOut.model_validate(p) for p in time_periods],
        line_items=[LineItemOut.model_validate(li) for li in line_items],
        cells=cells,
    )


@router.post("/{model_id}/calculate", response_model=GridResponse)
def calculate(model_id: int, scenario_id: int, db: Session = Depends(get_db)):
    scenario = db.query(Scenario).filter_by(id=scenario_id, model_id=model_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    Evaluator(db, model_id, scenario_id).run()
    return _build_grid_response(model_id, scenario_id, db)


@router.get("/{model_id}/grid", response_model=GridResponse)
def get_grid(model_id: int, scenario_id: int, db: Session = Depends(get_db)):
    return _build_grid_response(model_id, scenario_id, db)
