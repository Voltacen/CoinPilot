from flask import Flask

from Config import Config
from app.extensions import csrf, db, limiter, login_manager, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from app.api import api_v1_bp
    from app.views.admin_views import admin_bp
    from app.views.auth_views import auth_bp
    from app.views.dashboard_views import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_v1_bp, url_prefix="/api/v1")

    from commands.bootstrap import bootstrap_cli
    app.cli.add_command(bootstrap_cli)

    return app


app = create_app()
