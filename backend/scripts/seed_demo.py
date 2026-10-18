"""Seed/demo script to create admin user and admin wallet with large default balance."""
from backend.app import create_app
from backend.extensions import db
from backend.models import User, Wallet, AuditLog
from backend.config import Config
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    admin_email = 'admin@ledgerlocket.local'
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(email=admin_email, password_hash=generate_password_hash('adminpass'), roles=['admin'], verified_email=True)
        db.session.add(admin)
        db.session.commit()
        print('created admin user', admin.email)
    # create admin wallet
    admin_wallet_addr = 'LEDGER_ADMIN'
    w = Wallet.query.get(admin_wallet_addr)
    if not w:
        w = Wallet(address=admin_wallet_addr, user_id=admin.id, balance=0)
        db.session.add(w)
    # credit default supply
    default_supply = Config.DEFAULT_ADMIN_CREDIT_SUPPLY
    from decimal import Decimal
    w.balance = Decimal(str(w.balance or 0)) + Decimal(str(default_supply))
    db.session.add(w)
    db.session.commit()
    print('seeded admin wallet', admin_wallet_addr, 'with', default_supply)
