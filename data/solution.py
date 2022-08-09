import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Solution(SqlAlchemyBase):
    __tablename__ = 'solutions'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    theme = sqlalchemy.Column(sqlalchemy.String)

    author_thinks_false = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    is_true = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    is_false = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    think_is_false = sqlalchemy.Column(sqlalchemy.PickleType, default=[])
    think_is_true = sqlalchemy.Column(sqlalchemy.PickleType, default=[])

    rank = sqlalchemy.Column(sqlalchemy.Float, default=0)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User')
    # image_id = sqlalchemy.Column(sqlalchemy.Integer)
    problem_id = sqlalchemy.Column(sqlalchemy.Integer,
                                   sqlalchemy.ForeignKey("problems.id"))
    problem = orm.relation('Problem')

    comments = orm.relation("Comment", back_populates='solution')

    liked_by = sqlalchemy.Column(sqlalchemy.PickleType, default=[])

    image_ids = sqlalchemy.Column(sqlalchemy.PickleType, default=[])
