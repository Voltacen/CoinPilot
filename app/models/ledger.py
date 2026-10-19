import uuid
from datetime import datetime, timezone
from decimal import Decimal

from app.extensions import db


class InternalCreditAccount(db.Model):
    __tablename__ = "internal_credit_accounts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True, index=True)
    balance = db.Column(db.Numeric(precision=28, scale=4), nullable=False, default=Decimal("0.0000"))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User", back_populates="credit_account")


class CreditLedgerEntry(db.Model):
    __tablename__ = "credit_ledger_entries"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_account_id = db.Column(db.String(36), db.ForeignKey("internal_credit_accounts.id"), nullable=True, index=True)
    destination_account_id = db.Column(db.String(36), db.ForeignKey("internal_credit_accounts.id"), nullable=True, index=True)
    amount = db.Column(db.Numeric(precision=28, scale=4), nullable=False)
    entry_type = db.Column(db.String(32), nullable=False)
    idempotency_key = db.Column(db.String(128), unique=True, nullable=False, index=True)
    reference_note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
