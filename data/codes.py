import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase



# Код регистрации
class RegCode(SqlAlchemyBase):
    __tablename__ = 'codes'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    code = sqlalchemy.Column(sqlalchemy.String, unique=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    status = sqlalchemy.Column(sqlalchemy.String)

