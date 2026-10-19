import uuid
from decimal import Decimal

from app.extensions import db
from app.models.audit import AuditLog, Notification
from app.models.ledger import CreditLedgerEntry, InternalCreditAccount


class LedgerService:
    @staticmethod
    def transfer_internal_credit(sender_user_id: str, recipient_email: str, amount: Decimal, idempotency_key: str):
        if amount <= Decimal("0"):
            raise ValueError("Transfer amount must be strictly positive.")
        if CreditLedgerEntry.query.filter_by(idempotency_key=idempotency_key).first():
            raise ValueError("Duplicate request: Idempotency key already executed.")

        from app.models.user import User

        recipient = User.query.filter_by(email=recipient_email).first()
        if not recipient:
            raise ValueError(f"Recipient {recipient_email} not found.")
        if sender_user_id == recipient.id:
            raise ValueError("Sender and recipient cannot be identical.")

        sender_account = InternalCreditAccount.query.filter_by(user_id=sender_user_id).with_for_update().first()
        recipient_account = InternalCreditAccount.query.filter_by(user_id=recipient.id).with_for_update().first()

        if not sender_account or sender_account.balance < amount:
            raise ValueError("Insufficient internal credit balance.")

        if not recipient_account:
            recipient_account = InternalCreditAccount(user_id=recipient.id, balance=Decimal("0.0000"))
            db.session.add(recipient_account)
            db.session.flush()

        sender_account.balance -= amount
        recipient_account.balance += amount

        entry = CreditLedgerEntry(
            source_account_id=sender_account.id,
            destination_account_id=recipient_account.id,
            amount=amount,
            entry_type="TRANSFER",
            idempotency_key=idempotency_key,
            reference_note=f"Peer transfer to {recipient_email}",
        )
        db.session.add(entry)
        db.session.add(Notification(
            user_id=recipient.id,
            title="Internal Credits Received",
            message=f"You received {amount:,.4f} platform credits from an internal transfer.",
            category="SUCCESS",
        ))
        db.session.commit()
        return entry

    @staticmethod
    def adjust_user_credit(operator_user_id: str, target_user_id: str, amount: Decimal, note: str):
        target_account = InternalCreditAccount.query.filter_by(user_id=target_user_id).with_for_update().first()
        if not target_account:
            target_account = InternalCreditAccount(user_id=target_user_id, balance=Decimal("0.0000"))
            db.session.add(target_account)
            db.session.flush()

        if target_account.balance + amount < Decimal("0"):
            raise ValueError("Resulting balance cannot be negative.")

        target_account.balance += amount
        idempotency_key = f"adj_{uuid.uuid4().hex}"

        entry = CreditLedgerEntry(
            source_account_id=None if amount > 0 else target_account.id,
            destination_account_id=target_account.id if amount > 0 else None,
            amount=abs(amount),
            entry_type="ADMIN_ADJUSTMENT",
            idempotency_key=idempotency_key,
            reference_note=note,
        )
        db.session.add(entry)
        db.session.add(AuditLog(
            user_id=operator_user_id,
            action="CREDIT_ADJUSTMENT",
            target_entity=f"Account:{target_account.id}",
            details=f"Adjusted balance by {amount}. Note: {note}",
        ))
        db.session.commit()

    @staticmethod
    def get_ledger_history_for_user(user_id: str, limit: int = 25):
        account = InternalCreditAccount.query.filter_by(user_id=user_id).first()
        if not account:
            return []
        return CreditLedgerEntry.query.filter(
            (CreditLedgerEntry.source_account_id == account.id) |
            (CreditLedgerEntry.destination_account_id == account.id)
        ).order_by(CreditLedgerEntry.created_at.desc()).limit(limit).all()
