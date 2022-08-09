import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Problem(SqlAlchemyBase):
    __tablename__ = 'problems'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    rank = sqlalchemy.Column(sqlalchemy.Float, default=0)
    theme = sqlalchemy.Column(sqlalchemy.String)
    notauthor = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    author_thinks_false = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    is_true = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    is_false = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    think_is_false = sqlalchemy.Column(sqlalchemy.PickleType, default=[])
    think_is_true = sqlalchemy.Column(sqlalchemy.PickleType, default=[])

    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User')
    # image_id = sqlalchemy.Column(sqlalchemy.Integer)
    comments = orm.relation("Comment", back_populates='problem')

    solutions = orm.relation("Solution", back_populates='problem')

    liked_by = sqlalchemy.Column(sqlalchemy.PickleType, default=[])

    image_ids = sqlalchemy.Column(sqlalchemy.PickleType, default=[])
