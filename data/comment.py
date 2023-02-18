import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase

# Комментарий
class Comment(SqlAlchemyBase):
    __tablename__ = 'comments'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    original_text = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    rank = sqlalchemy.Column(sqlalchemy.Float, default=0)

    pdf_name = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    theme = sqlalchemy.Column(sqlalchemy.String)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User', back_populates='comments')
    # image_id = sqlalchemy.Column(sqlalchemy.Integer)
    post_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("posts.id"))
    post = orm.relation('Post', back_populates='comments')
    problem_id = sqlalchemy.Column(sqlalchemy.Integer,
                                   sqlalchemy.ForeignKey("problems.id"))
    problem = orm.relation('Problem', back_populates='comments')
    solution_id = sqlalchemy.Column(sqlalchemy.Integer,
                                    sqlalchemy.ForeignKey("solutions.id"))
    solution = orm.relation('Solution', back_populates='comments')

    liked_by = sqlalchemy.Column(sqlalchemy.PickleType, default=[])

    files = orm.relation("UsersFile", back_populates='comment')

    def get_rank(self):
        return int(self.rank*1000)/1000

    def get_parent(self):
        if self.post is not None:
            return ("post", self.post_id)
        if self.problem is not None:
            return ("problem", self.problem_id)
        if self.solution is not None:
            return ("solution", self.solution_id)

    def get_great_parent(self):
        if self.post is not None:
            return ("post", self.post_id)
        if self.problem is not None:
            return ("problem", self.problem_id)
        if self.solution is not None:
            return ("problem", self.solution.problem_id)
