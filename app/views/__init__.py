from app.views.auth_views import auth_bp
from app.views.admin_views import admin_bp
from app.views.dashboard_views import dashboard_bp
from app.api import api_v1_bp

__all__ = ["auth_bp", "admin_bp", "dashboard_bp", "api_v1_bp"]
