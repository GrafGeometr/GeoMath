import datetime
import math
import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    status = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String,
                              index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    wrong = sqlalchemy.Column(sqlalchemy.PickleType, default=[])

    toread = sqlalchemy.Column(sqlalchemy.PickleType, default=[])

    subscribers_count = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    readers = sqlalchemy.Column(sqlalchemy.PickleType, default=[])
    subscribes = sqlalchemy.Column(sqlalchemy.PickleType, default=[])

    posts = orm.relation("Post", back_populates='user')
    problems = orm.relation("Problem", back_populates='user')
    solutions = orm.relation("Solution", back_populates='user')
    comments = orm.relation("Comment", back_populates='user')

    def profile_href(self):
        return f"/profile/{self.id}"

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def get_rank(self, theme=None, creating_only=False):
        res = 0
        if self.status in ['жюри', 'преподаватель']:
            return 100
        for post in self.posts:
            if theme == None or post.theme == theme:
                res += post.rank
        for problem in self.problems:
            if theme == None or problem.theme == theme:
                res += problem.rank * 0.5
                if problem.author_thinks_false:
                    res -= 50
                elif problem.is_false:
                    res -= 100
        for solution in self.solutions:
            if not creating_only and theme == None or solution.theme == theme:
                res += solution.rank
                for other_solution in solution.problem.solutions:
                    if other_solution.id == solution.id and not solution.is_false:
                        res += 0.5 * solution.problem.rank
                        if solution.author_thinks_false:
                            res -= 25
                        elif solution.is_false:
                            res -= 50
                        break
                    elif not other_solution.is_false:
                        break
        for comment in self.comments:
            if theme == None or comment.theme == theme:
                res += comment.rank * 0.3
        timedelta = datetime.datetime.now() - self.created_date
        months = timedelta.seconds / 60 / 60 / 24 / 30
        res -= months
        # TODO fix reiting
        rank = max(1, math.atan(res / 2000) / math.pi * 200)
        return rank
