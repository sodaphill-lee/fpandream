import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.financial import Connection, IntegrationProvider
from app.services import myob_service

router = APIRouter(prefix="/api/myob", tags=["myob"])


@router.get("/connect/{organisation_id}")
def connect_myob(organisation_id: int):
    state = f"{organisation_id}:{secrets.token_urlsafe(16)}"
    url = myob_service.get_auth_url(state)
    return {"auth_url": url}


@router.get("/callback")
async def myob_callback(code: str, state: str, db: Session = Depends(get_db)):
    try:
        organisation_id = int(state.split(":")[0])
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    tokens = await myob_service.exchange_code_for_tokens(code)
    company_files = await myob_service.get_company_files(tokens["access_token"])

    if not company_files:
        raise HTTPException(status_code=400, detail="No MYOB company files found")

    company = company_files[0]

    connection = db.query(Connection).filter_by(
        organisation_id=organisation_id,
        provider=IntegrationProvider.myob,
    ).first()

    expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 1800))

    if connection:
        connection.access_token = tokens["access_token"]
        connection.refresh_token = tokens["refresh_token"]
        connection.token_expires_at = expires_at
        connection.provider_org_id = company.get("Uri", company.get("Id"))
        connection.provider_org_name = company.get("Name")
    else:
        connection = Connection(
            organisation_id=organisation_id,
            provider=IntegrationProvider.myob,
            provider_org_id=company.get("Uri", company.get("Id")),
            provider_org_name=company.get("Name"),
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_expires_at=expires_at,
        )
        db.add(connection)

    db.commit()
    return RedirectResponse(url=f"{settings.frontend_url}/connections?myob=connected")


@router.post("/sync/{connection_id}")
async def sync_myob(connection_id: int, db: Session = Depends(get_db)):
    connection = db.query(Connection).filter_by(
        id=connection_id, provider=IntegrationProvider.myob
    ).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    await myob_service.sync_accounts(connection, db)
    return {"message": "Sync complete", "last_synced_at": connection.last_synced_at}
