from flask import Blueprint
from flask import jsonify
from flask import request
from marshmallow import Schema
from marshmallow import ValidationError
from marshmallow import fields as maf
from marshmallow import validate as mav
from sqlalchemy import exists
from sqlalchemy import select

from db.db_models import Experiment
from db.db_models import Team
from db.db_models import get_session

bp = Blueprint('rec_task_resources', __name__, url_prefix='')
db_session = get_session()


class TeamSchema(Schema):
    id = maf.Integer()
    name = maf.String(required=True)
    experiments = maf.Nested("ExperimentSchema", many=True, dump_only=True, exclude=['teams'])


class ExperimentSchema(Schema):
    id = maf.Integer()
    description = maf.String(required=True)
    sample_ratio = maf.Integer(required=True)
    teams = maf.Nested(
        "TeamSchema", many=True, validate=mav.Length(1, 2), required=True, exclude=['experiments']
    )


@bp.route("/experiments")
def get_experiments():
    return '', 200


@bp.route("/experiments", methods=["POST"])
def create_experiment():

    try:
        item = ExperimentSchema().load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    teams = (
        db_session.execute(select(Team).where(Team.id.in_({team['id'] for team in item['teams']})))
        .scalars()
        .all()
    )

    if len(teams) != len({team['id'] for team in item['teams']}):
        return 'Some/All of the teams specified were not found', 400

    experiment = Experiment(
        description=item['description'], sample_ratio=item['sample_ratio'], teams=teams
    )

    db_session.add(experiment)
    db_session.commit()

    return ExperimentSchema().dump(experiment), 201


@bp.route("/teams", methods=["POST"])
def create_team():

    try:
        item = TeamSchema().load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    if db_session.execute(select(exists().where(Team.name == item['name']))).scalar():
        return 'Team already exists', 400

    team = Team(name=item['name'])

    db_session.add(team)
    db_session.commit()

    return TeamSchema().dump(team), 201
