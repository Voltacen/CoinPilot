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
    # require admin role
    actor_id = get_jwt_identity()
    from ..models import User
    user = User.query.get(actor_id)
    if not user or 'admin' not in (user.roles or []):
        return jsonify({'msg':'admin role required'}), 403

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
    tx = Transaction(from_addr='LEDGER_ADMIN', to_addr=to_address, amount=amt, type='mint', status='completed', data={'memo':memo})
    w.credit(amt)
    db.session.add(tx)
    # audit
    audit = AuditLog(actor_id=actor_id, action='mint', object_type='transaction', object_id=tx.tx_ref, reason=memo or '')
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

@bp.route('/transfer', methods=['POST'])
@jwt_required()
def transfer():
    actor_id = get_jwt_identity()
    data = request.get_json() or {}
    from_addr = data.get('from_address')
    to_addr = data.get('to_address')
    amount = data.get('amount')
    memo = data.get('memo')
    if not from_addr or not to_addr or not amount:
        return jsonify({'msg':'from_address, to_address, amount required'}), 400
    try:
        amt = Decimal(str(amount))
    except Exception:
        return jsonify({'msg':'invalid amount'}), 400
    # verify ownership of from wallet
    w = Wallet.query.get(from_addr)
    if not w or w.user_id != actor_id:
        return jsonify({'msg':'from address not owned by you'}), 403
    try:
        w.debit(amt)
    except ValueError:
        return jsonify({'msg':'insufficient balance'}), 400
    # ensure recipient wallet exists
    r = Wallet.query.get(to_addr)
    if not r:
        r = Wallet(address=to_addr, balance=0)
        db.session.add(r)
    r.credit(amt)
    tx = Transaction(from_addr=from_addr, to_addr=to_addr, amount=amt, type='transfer', status='completed', data={'memo': memo})
    db.session.add(tx)
    audit = AuditLog(actor_id=actor_id, action='transfer', object_type='transaction', object_id=tx.tx_ref, reason=memo or '')
    db.session.add(audit)
    note = Notification(wallet_address=to_addr, type='credit', payload={'amount':str(amt), 'tx_ref': tx.tx_ref, 'from': from_addr})
    db.session.add(note)
    db.session.commit()
    socketio.emit('wallet_update', {'address': to_addr, 'balance': str(r.balance)})
    enqueue_receipt_screenshot(tx.tx_ref)
    return jsonify({'tx_ref': tx.tx_ref}), 201
