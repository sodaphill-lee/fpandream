from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.models.financial import IntegrationProvider, AccountType


class OrganisationCreate(BaseModel):
    name: str


class OrganisationOut(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConnectionOut(BaseModel):
    id: int
    organisation_id: int
    provider: IntegrationProvider
    provider_org_name: Optional[str]
    last_synced_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AccountOut(BaseModel):
    id: int
    code: Optional[str]
    name: str
    account_type: Optional[AccountType]
    description: Optional[str]

    class Config:
        from_attributes = True


class TransactionOut(BaseModel):
    id: int
    date: datetime
    description: Optional[str]
    amount: float
    currency: str
    account_id: Optional[int]

    class Config:
        from_attributes = True
