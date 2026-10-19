from decimal import Decimal

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.audit import Notification
from app.models.blockchain import BlockchainTransaction
from app.models.ledger import CreditLedgerEntry, InternalCreditAccount
from app.services.blockchain_service import BlockchainService
from app.services.ledger_service import LedgerService


dashboard_bp = Blueprint("dashboard_views", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    account = InternalCreditAccount.query.filter_by(user_id=current_user.id).first()

    ledger_entries = []
    if account:
        ledger_entries = CreditLedgerEntry.query.filter(
            (CreditLedgerEntry.source_account_id == account.id) |
            (CreditLedgerEntry.destination_account_id == account.id)
        ).order_by(CreditLedgerEntry.created_at.desc()).limit(10).all()

    blockchain_txs = BlockchainTransaction.query.filter_by(user_id=current_user.id).order_by(BlockchainTransaction.created_at.desc()).limit(10).all()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()

    onchain_balance = Decimal("0.0")
    try:
        onchain_balance = BlockchainService.get_platform_native_balance(11155111)
    except Exception:
        pass

    return render_template(
        "dashboard/index.html",
        credit_account=account,
        ledger_entries=ledger_entries,
        blockchain_transactions=blockchain_txs,
        notifications=notifications,
        onchain_balance=onchain_balance,
    )


@dashboard_bp.route("/ledger/export-csv")
@login_required
def export_ledger_csv():
    account = InternalCreditAccount.query.filter_by(user_id=current_user.id).first()
    if not account:
        return Response("No ledger history available.", mimetype="text/plain")

    entries = CreditLedgerEntry.query.filter(
        (CreditLedgerEntry.source_account_id == account.id) |
        (CreditLedgerEntry.destination_account_id == account.id)
    ).order_by(CreditLedgerEntry.created_at.desc()).all()

    lines = ["created_at,entry_type,amount,direction,reference_note,source_account_id,destination_account_id"]
    for entry in entries:
        direction = "outgoing" if entry.source_account_id == account.id else "incoming"
        lines.append(
            f"{entry.created_at.isoformat()},{entry.entry_type},{entry.amount},{direction},{(entry.reference_note or '').replace(',', ';')},{entry.source_account_id or ''},{entry.destination_account_id or ''}"
        )

    csv_response = Response("\n".join(lines), mimetype="text/csv")
    csv_response.headers["Content-Disposition"] = "attachment; filename=coinpilot_ledger_history.csv"
    return csv_response
