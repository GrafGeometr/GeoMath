import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


# Лог
class Log(SqlAlchemyBase):
    __tablename__ = 'logs'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    message = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)