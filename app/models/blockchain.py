import uuid
from datetime import datetime, timezone

from app.extensions import db


class BlockchainTransaction(db.Model):
    __tablename__ = "blockchain_transactions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    chain_id = db.Column(db.BigInteger, nullable=False, index=True)
    token_symbol = db.Column(db.String(16), nullable=False)
    token_address = db.Column(db.String(42), nullable=True)
    sender_address = db.Column(db.String(42), nullable=False)
    recipient_address = db.Column(db.String(42), nullable=False, index=True)
    amount_in_units = db.Column(db.Numeric(precision=36, scale=18), nullable=False)
    tx_hash = db.Column(db.String(66), unique=True, nullable=True, index=True)
    nonce = db.Column(db.BigInteger, nullable=True)
    status = db.Column(db.String(24), nullable=False, default="Created", index=True)
    block_number = db.Column(db.BigInteger, nullable=True)
    gas_used = db.Column(db.Numeric(precision=20, scale=0), nullable=True)
    effective_gas_price = db.Column(db.Numeric(precision=30, scale=0), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    idempotency_key = db.Column(db.String(128), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)
