from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class IntegrationProvider(str, enum.Enum):
    xero = "xero"
    myob = "myob"


class Organisation(Base):
    __tablename__ = "organisations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    connections = relationship("Connection", back_populates="organisation")
    accounts = relationship("Account", back_populates="organisation")
    transactions = relationship("Transaction", back_populates="organisation")
    models = relationship("FinancialModel", back_populates="organisation")


class Connection(Base):
    """OAuth2 connection to an external provider (Xero, MYOB)."""
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    organisation_id = Column(Integer, ForeignKey("organisations.id"), nullable=False)
    provider = Column(Enum(IntegrationProvider), nullable=False)
    provider_org_id = Column(String)          # e.g. Xero tenant ID
    provider_org_name = Column(String)
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    last_synced_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    organisation = relationship("Organisation", back_populates="connections")


class AccountType(str, enum.Enum):
    asset = "asset"
    liability = "liability"
    equity = "equity"
    revenue = "revenue"
    expense = "expense"


class Account(Base):
    """Chart of accounts entry."""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    organisation_id = Column(Integer, ForeignKey("organisations.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("connections.id"))
    provider_account_id = Column(String)      # ID from Xero/MYOB
    code = Column(String)
    name = Column(String, nullable=False)
    account_type = Column(Enum(AccountType))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    organisation = relationship("Organisation", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")


class Transaction(Base):
    """Normalised financial transaction."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    organisation_id = Column(Integer, ForeignKey("organisations.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("connections.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"))
    provider_transaction_id = Column(String)
    date = Column(DateTime, nullable=False)
    description = Column(Text)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="AUD")
    created_at = Column(DateTime, default=datetime.utcnow)

    organisation = relationship("Organisation", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
