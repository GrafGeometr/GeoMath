import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Post(SqlAlchemyBase):
    __tablename__ = 'posts'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    theme = sqlalchemy.Column(sqlalchemy.String)
    rank = sqlalchemy.Column(sqlalchemy.Float,default=0)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User')
    # image_id = sqlalchemy.Column(sqlalchemy.Integer)
    comments = orm.relation("Comment", back_populates='post')

    liked_by = sqlalchemy.Column(sqlalchemy.PickleType, nullable=True)

    image_ids = sqlalchemy.Column(sqlalchemy.PickleType, nullable=True)
