import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.financial import Connection, IntegrationProvider
from app.services import xero_service

router = APIRouter(prefix="/api/xero", tags=["xero"])


@router.get("/connect/{organisation_id}")
def connect_xero(organisation_id: int):
    state = f"{organisation_id}:{secrets.token_urlsafe(16)}"
    url = xero_service.get_auth_url(state)
    return {"auth_url": url}


@router.get("/callback")
async def xero_callback(code: str, state: str, db: Session = Depends(get_db)):
    try:
        organisation_id = int(state.split(":")[0])
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    tokens = await xero_service.exchange_code_for_tokens(code)
    tenants = await xero_service.get_tenants(tokens["access_token"])

    if not tenants:
        raise HTTPException(status_code=400, detail="No Xero organisations found")

    tenant = tenants[0]

    connection = db.query(Connection).filter_by(
        organisation_id=organisation_id,
        provider=IntegrationProvider.xero,
    ).first()

    expires_at = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])

    if connection:
        connection.access_token = tokens["access_token"]
        connection.refresh_token = tokens["refresh_token"]
        connection.token_expires_at = expires_at
        connection.provider_org_id = tenant["tenantId"]
        connection.provider_org_name = tenant["tenantName"]
    else:
        connection = Connection(
            organisation_id=organisation_id,
            provider=IntegrationProvider.xero,
            provider_org_id=tenant["tenantId"],
            provider_org_name=tenant["tenantName"],
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_expires_at=expires_at,
        )
        db.add(connection)

    db.commit()
    return RedirectResponse(url=f"{settings.frontend_url}/connections?xero=connected")


@router.post("/sync/{connection_id}")
async def sync_xero(connection_id: int, db: Session = Depends(get_db)):
    connection = db.query(Connection).filter_by(
        id=connection_id, provider=IntegrationProvider.xero
    ).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    await xero_service.sync_accounts(connection, db)
    await xero_service.sync_transactions(connection, db)
    return {"message": "Sync complete", "last_synced_at": connection.last_synced_at}
