from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.financial import Organisation, Connection
from app.schemas.financial import OrganisationCreate, OrganisationOut, ConnectionOut

router = APIRouter(prefix="/api/organisations", tags=["organisations"])


@router.post("/", response_model=OrganisationOut)
def create_organisation(payload: OrganisationCreate, db: Session = Depends(get_db)):
    org = Organisation(name=payload.name)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@router.get("/", response_model=list[OrganisationOut])
def list_organisations(db: Session = Depends(get_db)):
    return db.query(Organisation).all()


@router.get("/{org_id}", response_model=OrganisationOut)
def get_organisation(org_id: int, db: Session = Depends(get_db)):
    org = db.query(Organisation).filter_by(id=org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return org


@router.get("/{org_id}/connections", response_model=list[ConnectionOut])
def get_connections(org_id: int, db: Session = Depends(get_db)):
    return db.query(Connection).filter_by(organisation_id=org_id).all()
