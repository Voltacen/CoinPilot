from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BigInteger

from flask import Flask
from config import Config

# keep models minimal; migrations will be added via Flask-Migrate
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accounts = db.relationship('Account', backref='user')

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    external_address = db.Column(db.String(128), nullable=True)
    balance = db.Column(BigInteger, default=0)
    currency = db.Column(db.String(32), default='TESTCOIN')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    from_account = db.Column(db.Integer, nullable=True)
    to_account = db.Column(db.Integer, nullable=True)
    to_external_address = db.Column(db.String(128), nullable=True)
    amount = db.Column(BigInteger, nullable=False)
    type = db.Column(db.String(32))
    status = db.Column(db.String(32), default='completed')
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ExternalAddressCredit(db.Model):
    __tablename__ = 'external_address_credits'
    id = db.Column(db.Integer, primary_key=True)
    external_address = db.Column(db.String(128), nullable=False)
    amount = db.Column(BigInteger, nullable=False)
    note = db.Column(db.Text, nullable=True)
    alert_sent = db.Column(db.Boolean, default=False)
    claimed = db.Column(db.Boolean, default=False)
    claimed_by_user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    external_address = db.Column(db.String(128), nullable=True)
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
