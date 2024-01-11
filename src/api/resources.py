from flask import Blueprint, jsonify
from flask import request
from marshmallow import Schema, ValidationError
from marshmallow import fields as maf
from marshmallow import validate as mav
from db.db_models import Experiment
from db.db_models import Team

bp = Blueprint('experiments', __name__, url_prefix='/experiments')


class TeamSchema(Schema):
    id = maf.Integer()
    name = maf.String(required=True)
    experiments = maf.Nested("ExperimentSchema", many=True)


class ExperimentSchema(Schema):
    id = maf.Integer()
    description = maf.String(required=True)
    sample_ratio = maf.Integer(required=True)
    teams = maf.Nested("TeamSchema", many=True, validate=mav.Length(1, 2), required=True)


@bp.route("")
def get_experiments():
    return '', 200


@bp.route("", methods=["POST"])
def create_experiment():

    try:
        item = ExperimentSchema().load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    experiment = db.d.Experiment()

    return '', 201
