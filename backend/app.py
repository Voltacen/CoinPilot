# Simple Flask app factory and blueprint registration
from flask import Flask
from .config import Config
from .extensions import db, migrate, jwt, socketio


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # register blueprints
    from .auth.routes import bp as auth_bp
    from .transactions.routes import bp as tx_bp
    from .receipts.receipt_screenshot import bp as receipts_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(tx_bp, url_prefix="/transactions")
    app.register_blueprint(receipts_bp, url_prefix="/receipts")

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}

    return app
