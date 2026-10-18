from .extensions import db
from datetime import datetime
import uuid
from decimal import Decimal

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    roles = db.Column(db.JSON, default=list)
    phone = db.Column(db.String(32), nullable=True)
    verified_email = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    wallets = db.relationship('Wallet', back_populates='user')

class Wallet(db.Model):
    __tablename__ = 'wallets'
    address = db.Column(db.String(128), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    label = db.Column(db.String(255), nullable=True)
    balance = db.Column(db.Numeric(60, 8), default=0)
    metadata = db.Column(db.JSON, default=dict)
    flagged = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='wallets')

    def credit(self, amount):
        # amount is Decimal
        cur = Decimal(str(self.balance or 0))
        self.balance = cur + amount

    def debit(self, amount):
        cur = Decimal(str(self.balance or 0))
        if cur < amount:
            raise ValueError('insufficient balance')
        self.balance = cur - amount

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    tx_ref = db.Column(db.String(64), unique=True, default=lambda: str(uuid.uuid4()))
    from_addr = db.Column(db.String(128), nullable=True)
    to_addr = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Numeric(60,8), nullable=False)
    type = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(32), default='completed')
    data = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(64), nullable=False)
    payload = db.Column(db.JSON, default=dict)
    delivered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(128), nullable=False)
    object_type = db.Column(db.String(64), nullable=True)
    object_id = db.Column(db.String(128), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    metadata = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ApiKey(db.Model):
    __tablename__ = 'api_keys'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), nullable=False)
    owner_id = db.Column(db.Integer, nullable=True)
    scopes = db.Column(db.JSON, default=list)
    rate_limit = db.Column(db.Integer, default=1000)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Integration(db.Model):
    __tablename__ = 'integrations'
    id = db.Column(db.Integer, primary_key=True)
    exchange_name = db.Column(db.String(64), nullable=False)
    credentials_encrypted = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='disabled')
    last_sync = db.Column(db.DateTime, nullable=True)

class KycProfile(db.Model):
    __tablename__ = 'kyc_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(32), default='pending')
    documents = db.Column(db.JSON, default=list)
    reviewed_by = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LoginNonce(db.Model):
    __tablename__ = 'login_nonces'
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(128), nullable=False, index=True)
    nonce = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
