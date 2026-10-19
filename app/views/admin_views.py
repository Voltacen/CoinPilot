from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.audit import AuditLog
from app.models.blockchain import BlockchainTransaction
from app.models.user import User
from app.services.ledger_service import LedgerService


admin_bp = Blueprint("admin_views", __name__)


@admin_bp.before_request
@login_required
def restrict_to_admin():
    if not current_user.is_admin:
        flash("Unauthorized: Administrator access required.", "danger")
        return redirect(url_for("dashboard_views.index"))


@admin_bp.route("/")
def index():
    total_users = User.query.count()
    total_txs = BlockchainTransaction.query.count()
    audit_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()
    return render_template("admin/index.html", total_users=total_users, total_txs=total_txs, audit_logs=audit_logs)


@admin_bp.route("/adjust-credits", methods=["POST"])
def adjust_credits():
    target_email = request.form.get("target_email", "").strip().lower()
    amount_raw = request.form.get("amount", "0")
    ref_note = request.form.get("reference_note", "Administrative adjustment")

    try:
        amount = Decimal(amount_raw)
        target_user = User.query.filter_by(email=target_email).first()
        if not target_user:
            flash(f"User with email {target_email} does not exist.", "danger")
            return redirect(url_for("admin_views.index"))

        LedgerService.adjust_user_credit(
            operator_user_id=current_user.id,
            target_user_id=target_user.id,
            amount=amount,
            note=ref_note,
        )
        flash(f"Successfully adjusted credit balance by {amount} for {target_email}.", "success")
    except Exception as err:
        flash(f"Adjustment failed: {str(err)}", "danger")

    return redirect(url_for("admin_views.index"))
