import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.config import settings
from app.models.financial import Connection, Account, Transaction, IntegrationProvider, AccountType

XERO_AUTH_URL = "https://login.xero.com/identity/connect/authorize"
XERO_TOKEN_URL = "https://identity.xero.com/connect/token"
XERO_API_BASE = "https://api.xero.com/api.xro/2.0"
XERO_CONNECTIONS_URL = "https://api.xero.com/connections"

XERO_SCOPES = "openid profile email accounting.transactions accounting.reports.read accounting.journals.read accounting.settings offline_access"


def get_auth_url(state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.xero_client_id,
        "redirect_uri": settings.xero_redirect_uri,
        "scope": XERO_SCOPES,
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{XERO_AUTH_URL}?{query}"


async def exchange_code_for_tokens(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            XERO_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.xero_redirect_uri,
            },
            auth=(settings.xero_client_id, settings.xero_client_secret),
        )
        response.raise_for_status()
        return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            XERO_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            auth=(settings.xero_client_id, settings.xero_client_secret),
        )
        response.raise_for_status()
        return response.json()


async def get_tenants(access_token: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            XERO_CONNECTIONS_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


async def ensure_fresh_token(connection: Connection, db: Session) -> str:
    if connection.token_expires_at and connection.token_expires_at < datetime.utcnow():
        tokens = await refresh_access_token(connection.refresh_token)
        connection.access_token = tokens["access_token"]
        connection.refresh_token = tokens.get("refresh_token", connection.refresh_token)
        connection.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
        db.commit()
    return connection.access_token


async def sync_accounts(connection: Connection, db: Session):
    token = await ensure_fresh_token(connection, db)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{XERO_API_BASE}/Accounts",
            headers={
                "Authorization": f"Bearer {token}",
                "Xero-tenant-id": connection.provider_org_id,
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()

    xero_type_map = {
        "BANK": AccountType.asset,
        "CURRENT": AccountType.asset,
        "FIXED": AccountType.asset,
        "NONCURRENT": AccountType.asset,
        "CURRLIAB": AccountType.liability,
        "TERMLIAB": AccountType.liability,
        "EQUITY": AccountType.equity,
        "REVENUE": AccountType.revenue,
        "SALES": AccountType.revenue,
        "DIRECTCOSTS": AccountType.expense,
        "OVERHEADS": AccountType.expense,
        "EXPENSE": AccountType.expense,
    }

    for xero_account in data.get("Accounts", []):
        existing = db.query(Account).filter_by(
            connection_id=connection.id,
            provider_account_id=xero_account["AccountID"],
        ).first()

        account_type = xero_type_map.get(xero_account.get("Type", ""), None)

        if existing:
            existing.name = xero_account["Name"]
            existing.code = xero_account.get("Code")
            existing.account_type = account_type
            existing.description = xero_account.get("Description")
        else:
            db.add(Account(
                organisation_id=connection.organisation_id,
                connection_id=connection.id,
                provider_account_id=xero_account["AccountID"],
                code=xero_account.get("Code"),
                name=xero_account["Name"],
                account_type=account_type,
                description=xero_account.get("Description"),
            ))

    connection.last_synced_at = datetime.utcnow()
    db.commit()


async def sync_transactions(connection: Connection, db: Session):
    token = await ensure_fresh_token(connection, db)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{XERO_API_BASE}/BankTransactions",
            headers={
                "Authorization": f"Bearer {token}",
                "Xero-tenant-id": connection.provider_org_id,
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()

    for txn in data.get("BankTransactions", []):
        existing = db.query(Transaction).filter_by(
            connection_id=connection.id,
            provider_transaction_id=txn["BankTransactionID"],
        ).first()
        if existing:
            continue

        account = db.query(Account).filter_by(
            connection_id=connection.id,
            provider_account_id=txn.get("BankAccount", {}).get("AccountID"),
        ).first()

        db.add(Transaction(
            organisation_id=connection.organisation_id,
            connection_id=connection.id,
            account_id=account.id if account else None,
            provider_transaction_id=txn["BankTransactionID"],
            date=datetime.fromisoformat(txn["DateString"]) if "DateString" in txn else datetime.utcnow(),
            description=txn.get("Reference", ""),
            amount=txn.get("Total", 0.0),
            currency=txn.get("CurrencyCode", "AUD"),
        ))

    db.commit()
