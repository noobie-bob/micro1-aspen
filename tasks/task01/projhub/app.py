"""Flask application factory for ProjHub."""

import traceback

from flask import Flask, jsonify

from projhub.db import reset_state
from projhub.routes import (
    admin, attachments, comments, debug, projects, reports, search, tasks, teams,
)


def create_app() -> Flask:
    """Create and configure the ProjHub Flask application."""
    reset_state()
    app = Flask(__name__)
    app.config["TESTING"] = False

    # Register route blueprints
    app.register_blueprint(teams.bp)
    app.register_blueprint(projects.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(comments.bp)
    app.register_blueprint(attachments.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(search.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(debug.bp)

    # ── BUG: Verbose error handler leaks internal details ──────────────
    @app.errorhandler(Exception)
    def handle_exception(e):
        """BUG: returns full stack trace and internal paths to caller.
        Should return a generic error message in production."""
        tb = traceback.format_exc()
        return jsonify({
            "error": str(e),
            "type": type(e).__name__,
            "traceback": tb,
        }), 500

    @app.errorhandler(404)
    def handle_404(e):
        """BUG: leaks framework version in error response."""
        import flask
        return jsonify({
            "error": "not found",
            "framework_version": flask.__version__,
        }), 404

    return app


app = create_app()
