from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.utils.response import error_response, success_response

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable Cross-Origin Resource Sharing
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health():
        return success_response(
            data={"status": "UP", "service": "Staff Attendance Portal API", "version": "2.0.0"},
            message="Service is healthy and responding."
        )

    # Register only active API blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.attendance_routes import attendance_bp
    from app.routes.employee_routes import employee_bp
    from app.routes.report_routes import report_bp
    from app.routes.settings_routes import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(settings_bp)

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found(e):
        return error_response("Endpoint not found.", 404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return error_response("HTTP method not allowed for this endpoint.", 405)

    @app.errorhandler(500)
    def server_error(e):
        return error_response("Internal server error occurred.", 500)

    return app
