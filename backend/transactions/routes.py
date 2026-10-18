from flask import Blueprint, request, jsonify, current_app, abort, send_file
from ..extensions import db, socketio
from ..models import Transaction, Wallet, AuditLog, Notification
from flask_jwt_extended import jwt_required, get_jwt_identity
from decimal import Decimal
from ..tasks.screenshot_task import enqueue_receipt_screenshot
from io import BytesIO

bp = Blueprint('transactions', __name__)

@bp.route('/', methods=['GET'])
def list_transactions():
    address = request.args.get('address')
    q = Transaction.query
    if address:
        q = q.filter((Transaction.to_addr == address) | (Transaction.from_addr == address))
    txs = q.order_by(Transaction.created_at.desc()).limit(100).all()
    return jsonify([{
        'tx_ref': t.tx_ref,
        'from': t.from_addr,
        'to': t.to_addr,
        'amount': str(t.amount),
        'type': t.type,
        'created_at': t.created_at.isoformat()
    } for t in txs])

@bp.route('/mint', methods=['POST'])
@jwt_required()
def mint():
    # Only allow admin roles in production; here simplified: any authenticated can mint for demo
    data = request.get_json() or {}
    to_address = data.get('to_address')
    amount = data.get('amount')
    memo = data.get('memo')
    if not to_address or not amount:
        return jsonify({'msg':'to_address and amount required'}), 400
    try:
        amt = Decimal(str(amount))
    except Exception:
        return jsonify({'msg':'invalid amount'}), 400
    # ensure wallet exists
    w = Wallet.query.get(to_address)
    if not w:
        w = Wallet(address=to_address, balance=0)
        db.session.add(w)
    # create transaction
    tx = Transaction(from_addr=None, to_addr=to_address, amount=amt, type='mint', status='completed', data={'memo':memo})
    w.balance = w.balance + amt
    db.session.add(tx)
    # audit
    audit = AuditLog(actor_id=get_jwt_identity(), action='mint', object_type='transaction', object_id=tx.tx_ref, reason=memo or '')
    db.session.add(audit)
    # notification
    note = Notification(wallet_address=to_address, type='credit', payload={'amount':str(amt), 'tx_ref': tx.tx_ref})
    db.session.add(note)
    db.session.commit()

    # emit socket notification
    socketio.emit('wallet_update', {'address': to_address, 'balance': str(w.balance)})

    # enqueue receipt screenshot generation (async)
    enqueue_receipt_screenshot(tx.tx_ref)

    return jsonify({'tx_ref': tx.tx_ref}), 201
