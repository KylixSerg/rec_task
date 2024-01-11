from flask import Blueprint
from flask import jsonify
from flask import request
from marshmallow import EXCLUDE
from marshmallow import Schema
from marshmallow import ValidationError
from marshmallow import fields as maf
from marshmallow import post_load
from marshmallow import pre_load
from marshmallow import validate as mav
from sqlalchemy import and_
from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy import exists
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.orm import selectinload

from db.db_models import Experiment
from db.db_models import Team
from db.db_models import experiments_teams
from db.db_models import get_session

bp = Blueprint('rec_task_resources', __name__, url_prefix='')


class TeamSchema(Schema):
    id = maf.Integer()
    name = maf.String(required=True)
    experiments = maf.Nested("ExperimentSchema", many=True, dump_only=True, exclude=['teams'])


class ExperimentSchema(Schema):
    id = maf.Integer()
    description = maf.String(required=True)
    sample_ratio = maf.Integer(required=True)
    teams = maf.Nested("TeamSchema", many=True, dump_only=True, exclude=['experiments'])
    team_ids = maf.List(maf.Integer(), load_only=True, required=True, validate=mav.Length(1, 2))


class BaseQueryArgsSchema(Schema):
    page = maf.Integer(load_default=0)
    limit = maf.Integer(load_default=25)
    order_by = maf.String(load_default='asc', validate=mav.OneOf(('asc', 'desc')))
    sort_by = maf.String()

    @post_load
    def normalize_qas(self, data, **kwargs):
        data['page'] = 0 if data['page'] < 0 else data['page']
        data['limit'] = 25 if data['limit'] < 1 else data['limit']
        if data['page'] > 0:
            data['page'] -= 1
        return data


class ExperimentListQAS(BaseQueryArgsSchema):
    sort_by = maf.String(validate=mav.OneOf(('id', 'sample_ratio')), load_default='id')

    class Meta:
        unknown = EXCLUDE


@bp.route("/experiments")
def get_experiments():
    """List experiments."""

    session = get_session()

    try:
        filters = ExperimentListQAS().load(request.args)
        # For a quick and dirty way to deserialize lists
        if team_ids := request.args.getlist("team_ids[]"):
            try:
                team_ids = [int(tid) for tid in team_ids]
                filters['team_ids[]'] = team_ids
            except ValueError as ex:
                return ValidationError(str(ex))
    except ValidationError as err:
        return jsonify(err.messages), 400

    order_by_func = asc if filters['order_by'] == 'asc' else desc

    query = (
        select(Experiment)
        .offset(filters['page'] * filters['limit'])
        .limit(filters['limit'])
        .order_by(order_by_func(text(f"{filters['sort_by']}")))
        .options(selectinload(Experiment.teams))
    )

    if team_ids:
        # TODO: extract to a MAT VIEW
        filter_query = (
            select(
                experiments_teams.c.experiment_id,
                func.array_agg(experiments_teams.c.team_id).label("team_ids"),
            )
            .group_by(experiments_teams.c.experiment_id)
            .cte()
        )

        query = query.join(
            filter_query,
            and_(
                filter_query.c.team_ids.op("&&")(team_ids),
                filter_query.c.experiment_id == Experiment.id,
            ),
        )

    data = ExperimentSchema(many=True).dump(session.execute(query).scalars())
    meta = {**filters, "items": len(data), "page": filters['page'] + 1}

    return {"data": data, "meta": meta}


@bp.route("/experiments", methods=["POST"])
def create_experiment():
    try:
        item = ExperimentSchema().load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    db_session = get_session()

    teams = db_session.execute(select(Team).where(Team.id.in_(item['team_ids']))).scalars().all()

    if len(teams) != len(item['team_ids']):
        return jsonify('Some/All of the teams specified were not found'), 400

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

    db_session = get_session()

    if db_session.execute(select(exists().where(Team.name == item['name']))).scalar():
        return jsonify('Team already exists'), 400

    team = Team(name=item['name'])

    db_session.add(team)
    db_session.commit()

    return TeamSchema().dump(team), 201
