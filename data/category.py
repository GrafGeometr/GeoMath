import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase

posts_and_cats_table = sqlalchemy.Table(
    'posts_and_cats',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('posts', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('posts.id')),
    sqlalchemy.Column('category', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('category.id'))
)

problems_and_cats_table = sqlalchemy.Table(
    'problems_and_cats',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('problems', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('problems.id')),
    sqlalchemy.Column('category', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('category.id'))
)


class Category(SqlAlchemyBase):
    __tablename__ = 'category'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=True)
    posts = orm.relation("Post",
                         secondary="posts_and_cats",
                         back_populates="categories")
    problems = orm.relation("Problem",
                            secondary="problems_and_cats",
                            back_populates="categories")
