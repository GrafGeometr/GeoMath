import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Post(SqlAlchemyBase):
    __tablename__ = 'post'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    post_type = sqlalchemy.Column(sqlalchemy.Boolean, nullable=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=True)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User')
    image_id = sqlalchemy.Column(sqlalchemy.Integer)
    original_solution_id = sqlalchemy.Column(sqlalchemy.Integer)
    # TODO fix ARRAY
    # solutions = sqlalchemy.Column(sqlalchemy.ARRAY)
    # comments = sqlalchemy.Column(sqlalchemy.ARRAY)