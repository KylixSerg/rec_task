from flask import Blueprint

bp = Blueprint('experiments', __name__, url_prefix='/experiments')


@bp.route("")
def get_experiments():
    return '', 200


@bp.route("", methods=["POST"])
def create_experiment():
    return '', 201
