from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..models import User
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

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
