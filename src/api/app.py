from flask import Flask
from flask import jsonify

from api.experiments import bp
from db.db_models import setup_db


def create_app():
    setup_db()

    app = Flask(__name__, static_folder=None)

    # Register blueprint
    app.register_blueprint(bp)

    # register an error handler

    # register a health endpoint
    @app.route("/health")
    def health():
        return jsonify(dict(status="OK")), 200

    return app


def run():
    app = create_app()
    app.run(host="0.0.0.0", port=8081)
