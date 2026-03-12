import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.config import settings
from app.models.financial import Connection, Account, Transaction, AccountType

MYOB_AUTH_URL = "https://secure.myob.com/oauth2/account/authorize"
MYOB_TOKEN_URL = "https://secure.myob.com/oauth2/v1/authorize"
MYOB_API_BASE = "https://api.myob.com/accountright"

MYOB_SCOPES = "CompanyFile"


def get_auth_url(state: str) -> str:
    params = {
        "client_id": settings.myob_client_id,
        "redirect_uri": settings.myob_redirect_uri,
        "response_type": "code",
        "scope": MYOB_SCOPES,
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{MYOB_AUTH_URL}?{query}"


async def exchange_code_for_tokens(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            MYOB_TOKEN_URL,
            data={
                "client_id": settings.myob_client_id,
                "client_secret": settings.myob_client_secret,
                "redirect_uri": settings.myob_redirect_uri,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            MYOB_TOKEN_URL,
            data={
                "client_id": settings.myob_client_id,
                "client_secret": settings.myob_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        response.raise_for_status()
        return response.json()


async def get_company_files(access_token: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            MYOB_API_BASE,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


async def ensure_fresh_token(connection: Connection, db: Session) -> str:
    if connection.token_expires_at and connection.token_expires_at < datetime.utcnow():
        tokens = await refresh_access_token(connection.refresh_token)
        connection.access_token = tokens["access_token"]
        connection.refresh_token = tokens.get("refresh_token", connection.refresh_token)
        connection.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 1800))
        db.commit()
    return connection.access_token


async def sync_accounts(connection: Connection, db: Session):
    token = await ensure_fresh_token(connection, db)
    company_file_uri = connection.provider_org_id

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{company_file_uri}/GeneralLedger/Account",
            headers={
                "Authorization": f"Bearer {token}",
                "x-myobapi-key": settings.myob_client_id,
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()

    myob_type_map = {
        "Asset": AccountType.asset,
        "Liability": AccountType.liability,
        "Equity": AccountType.equity,
        "Income": AccountType.revenue,
        "CostOfSales": AccountType.expense,
        "Expense": AccountType.expense,
        "OtherIncome": AccountType.revenue,
        "OtherExpense": AccountType.expense,
    }

    for acct in data.get("Items", []):
        existing = db.query(Account).filter_by(
            connection_id=connection.id,
            provider_account_id=acct["UID"],
        ).first()

        account_type = myob_type_map.get(acct.get("Classification"), None)

        if existing:
            existing.name = acct["Name"]
            existing.code = acct.get("DisplayID")
            existing.account_type = account_type
        else:
            db.add(Account(
                organisation_id=connection.organisation_id,
                connection_id=connection.id,
                provider_account_id=acct["UID"],
                code=acct.get("DisplayID"),
                name=acct["Name"],
                account_type=account_type,
            ))

    connection.last_synced_at = datetime.utcnow()
    db.commit()
