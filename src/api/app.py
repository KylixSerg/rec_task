from flask import Blueprint
from flask import Flask
from flask import jsonify

bp = Blueprint('rec_task_bp', __name__, url_prefix='')


def create_app():

    # setup db here

    app = Flask(__name__, static_folder=None)

    # Register blueprint
    app.register_blueprint(bp)

    # register an error handler

    return app


@bp.route("/health")
def health():
    return jsonify(dict(status="OK")), 200


def run():
    app = create_app()
    app.run(host="0.0.0.0", port=8081)
