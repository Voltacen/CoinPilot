from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..models import User, Wallet, LoginNonce
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from uuid import uuid4
from eth_account.messages import encode_defunct
from eth_account import Account

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'msg': 'email and password required'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'msg':'user exists'}), 400
    user = User(email=email, password_hash=generate_password_hash(password), verified_email=False)
    db.session.add(user)
    db.session.commit()
    # In prod send verification email
    return jsonify({'msg':'registered'}), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash or '', password):
        return jsonify({'msg':'bad credentials'}), 401
    access = create_access_token(identity=user.id)
    refresh = create_refresh_token(identity=user.id)
    return jsonify({'access': access, 'refresh': refresh}), 200

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    new_access = create_access_token(identity=identity)
    return jsonify({'access': new_access}), 200

@bp.route('/nonce')
def get_nonce():
    address = request.args.get('address')
    if not address:
        return jsonify({'msg':'address required'}), 400
    nonce = str(uuid4())
    ln = LoginNonce(address=address.lower(), nonce=nonce)
    db.session.add(ln)
    db.session.commit()
    return jsonify({'address': address, 'nonce': nonce}), 200

@bp.route('/wallet-login', methods=['POST'])
def wallet_login():
    data = request.get_json() or {}
    address = (data.get('address') or '').lower()
    signature = data.get('signature')
    if not address or not signature:
        return jsonify({'msg':'address and signature required'}), 400
    # get latest nonce
    ln = LoginNonce.query.filter_by(address=address).order_by(LoginNonce.created_at.desc()).first()
    if not ln:
        return jsonify({'msg':'nonce not found for address'}), 400
    message = encode_defunct(text=ln.nonce)
    try:
        recovered = Account.recover_message(message, signature=signature)
    except Exception as e:
        return jsonify({'msg':'signature verification failed', 'error': str(e)}), 400
    if recovered.lower() != address.lower():
        return jsonify({'msg':'signature does not match address'}), 400
    # find or create user tied to this wallet
    wallet = Wallet.query.get(address)
    user = None
    if wallet and wallet.user_id:
        user = User.query.get(wallet.user_id)
    if not user:
        # create an auto user for this wallet
        user_email = f"{address}@wallet.local"
        user = User(email=user_email, verified_email=True)
        db.session.add(user)
        db.session.flush()
        # create or attach wallet
        if not wallet:
            wallet = Wallet(address=address, user_id=user.id, balance=0)
            db.session.add(wallet)
        else:
            wallet.user_id = user.id
    db.session.commit()
    access = create_access_token(identity=user.id)
    refresh = create_refresh_token(identity=user.id)
    return jsonify({'access': access, 'refresh': refresh, 'user_id': user.id}), 200
