from celery import Celery
from config import Config
from models import db, User, Notification, ExternalAddressCredit
from flask import Flask
import smtplib
from email.message import EmailMessage

celery = None

def make_celery(app: Flask = None):
    global celery
    app = app or Flask(__name__)
    app.config.from_object(Config)
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# Define tasks
@make_celery(Flask(__name__)).task
def send_alert(payload):
    """payload: dict with type and details"""
    p = payload
    if p.get('type') == 'user_credit':
        user_id = p.get('user_id')
        amount = p.get('amount')
        note = p.get('note')
        n = Notification(user_id=user_id, message=f'Received {amount} TESTCOIN. {note or ""}')
        db.session.add(n)
        db.session.commit()
        # send email if user has an email
        user = User.query.get(user_id)
        if user and user.email:
            _send_email(user.email, 'You received TESTCOIN', n.message)
    elif p.get('type') == 'external_credit':
        addr = p.get('external_address')
        amount = p.get('amount')
        note = p.get('note')
        n = Notification(external_address=addr, message=f'Address {addr} received {amount} TESTCOIN (off-chain). {note or ""}')
        db.session.add(n)
        e = ExternalAddressCredit.query.filter_by(external_address=addr).order_by(ExternalAddressCredit.created_at.desc()).first()
        if e:
            e.alert_sent = True
            db.session.add(e)
        db.session.commit()
        # Attempt to send an email to admin or log - we don't know recipient email for external addresses.


def _send_email(to, subject, body):
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = Config.MAIL_DEFAULT_SENDER
        msg['To'] = to
        msg.set_content(body)
        if Config.MAIL_SERVER:
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as s:
                if Config.MAIL_USE_TLS:
                    s.starttls()
                if Config.MAIL_USERNAME and Config.MAIL_PASSWORD:
                    s.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                s.send_message(msg)
    except Exception as e:
        # keep failures non-fatal for now
        print('email error',e)
