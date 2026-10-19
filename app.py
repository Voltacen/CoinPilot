from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from config import Config
from models import db, User, Account, Transaction, ExternalAddressCredit, Notification
from web3 import Web3
from tasks import make_celery, send_alert
from passlib.hash import bcrypt
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
celery = make_celery(app)

# Simple helper
def get_or_create_account_for_user(user):
    acct = Account.query.filter_by(user_id=user.id).first()
    if not acct:
        acct = Account(user_id=user.id, balance=0)
        db.session.add(acct)
        db.session.commit()
    return acct

@app.route('/health')
def health():
    return jsonify({'status':'ok'})

@app.route('/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error':'email and password required'}),400
    if User.query.filter_by(email=email).first():
        return jsonify({'error':'email exists'}),400
    pw_hash = bcrypt.hash(password)
    user = User(email=email, password=pw_hash)
    db.session.add(user)
    db.session.commit()
    get_or_create_account_for_user(user)
    return jsonify({'msg':'registered','email':email}),201

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error':'email and password required'}),400
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error':'invalid creds'}),401
    if not bcrypt.verify(password, user.password):
        return jsonify({'error':'invalid creds'}),401
    access = create_access_token(identity={'id':user.id,'email':user.email,'is_admin':user.is_admin})
    return jsonify({'access_token':access})

@app.route('/accounts/me')
@jwt_required()
def me_account():
    identity = get_jwt_identity()
    user = User.query.get(identity['id'])
    acct = Account.query.filter_by(user_id=user.id).first()
    balance = acct.balance if acct else 0
    return jsonify({'email':user.email,'balance':int(balance),'currency':acct.currency if acct else 'TESTCOIN'})

@app.route('/profile/attach_address', methods=['POST'])
@jwt_required()
def attach_address():
    identity = get_jwt_identity()
    user = User.query.get(identity['id'])
    data = request.json or {}
    addr = data.get('address')
    if not addr:
        return jsonify({'error':'address required'}),400
    if not Web3.isAddress(addr):
        return jsonify({'error':'invalid address'}),400
    acct = get_or_create_account_for_user(user)
    acct.external_address = addr
    db.session.add(acct)
    db.session.commit()
    return jsonify({'msg':'address attached','address':addr})

@app.route('/claim', methods=['POST'])
@jwt_required()
def claim_external():
    identity = get_jwt_identity()
    user = User.query.get(identity['id'])
    data = request.json or {}
    addr = data.get('address')
    if not addr:
        return jsonify({'error':'address required'}),400
    # find unclaimed credits
    credits = ExternalAddressCredit.query.filter_by(external_address=addr,claimed=False).all()
    if not credits:
        return jsonify({'error':'no credits for this address'}),404
    acct = get_or_create_account_for_user(user)
    total = 0
    for c in credits:
        total += int(c.amount)
        c.claimed = True
        c.claimed_by_user = user.id
        db.session.add(c)
        tx = Transaction(from_account=None,to_account=acct.id,to_external_address=addr,amount=c.amount,type='claim',note=c.note)
        db.session.add(tx)
    acct.balance = (acct.balance or 0) + total
    db.session.commit()
    # notify user
    send_alert.delay({'type':'user_credit','user_id':user.id,'amount':total,'note':f'Claimed credits for {addr}'})
    return jsonify({'msg':'claimed','address':addr,'amount':total}),200

@app.route('/admin/send', methods=['POST'])
@jwt_required()
def admin_send():
    identity = get_jwt_identity()
    if not identity.get('is_admin'):
        return jsonify({'error':'admin only'}),403
    data = request.json or {}
    try:
        amount = int(data.get('amount',0))
    except Exception:
        return jsonify({'error':'invalid amount'}),400
    to_email = data.get('to_email')
    to_address = data.get('to_address')
    note = data.get('note')

    # find admin account
    admin_user = User.query.filter_by(is_admin=True).first()
    admin_acct = Account.query.filter_by(user_id=admin_user.id).first()
    if admin_acct.balance < amount:
        return jsonify({'error':'insufficient admin balance'}),400
    admin_acct.balance -= amount

    if to_email:
        user = User.query.filter_by(email=to_email).first()
        if not user:
            return jsonify({'error':'recipient not found'}),404
        acct = get_or_create_account_for_user(user)
        acct.balance += amount
        tx = Transaction(from_account=admin_acct.id,to_account=acct.id,amount=amount,type='credit',note=note)
        db.session.add(tx)
        db.session.commit()
        # notify recipient via celery
        send_alert.delay({'type':'user_credit','user_id':user.id,'amount':amount,'note':note})
        return jsonify({'msg':'credited user','to':to_email,'amount':amount}),200

    if to_address:
        # validate address (supports Ethereum-like)
        if not Web3.isAddress(to_address):
            return jsonify({'error':'invalid address'}),400
        ext = ExternalAddressCredit(external_address=to_address,amount=amount,note=note)
        db.session.add(ext)
        tx = Transaction(from_account=admin_acct.id,to_external_address=to_address,amount=amount,type='external_credit',note=note)
        db.session.add(tx)
        db.session.commit()
        send_alert.delay({'type':'external_credit','external_address':to_address,'amount':amount,'note':note})
        return jsonify({'msg':'credited external address (off-chain)','to':to_address,'amount':amount}),200

    return jsonify({'error':'to_email or to_address required'}),400

@app.route('/withdraw', methods=['POST'])
@jwt_required()
def withdraw():
    # withdrawals are disabled
    return jsonify({'error':'withdrawals are disabled for this platform (non-withdrawable credits)'}),403

@app.route('/notifications')
@jwt_required()
def list_notifications():
    identity = get_jwt_identity()
    user_id = identity['id']
    notes = Notification.query.filter((Notification.user_id==user_id)|(Notification.external_address!=None)).order_by(Notification.created_at.desc()).all()
    out = [{'id':n.id,'message':n.message,'read':n.read,'created_at':n.created_at.isoformat()} for n in notes]
    return jsonify(out)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0',port=5000,debug=True)
