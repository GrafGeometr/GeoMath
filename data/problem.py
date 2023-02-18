import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase

# Выделяем категории из текста
def get_categories_from_text(text):
    categories_names = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '#':
            j = 1
            name = []
            while i + j < n:
                if text[i + j] in '#\n \t,;':
                    break
                name.append(text[i + j])
                j += 1
            if name:
                categories_names.append(''.join(name))
            i += j
        else:
            i += 1
    return categories_names

# Задача
class Problem(SqlAlchemyBase):
    __tablename__ = 'problems'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    rank = sqlalchemy.Column(sqlalchemy.Float, default=0)
    theme = sqlalchemy.Column(sqlalchemy.String)
    pdf_name = sqlalchemy.Column(sqlalchemy.String, default="")
    notauthor = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    pdf_name = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    author_thinks_false = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    is_true = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    is_false = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    think_is_false = sqlalchemy.Column(sqlalchemy.PickleType, default=[])
    think_is_true = sqlalchemy.Column(sqlalchemy.PickleType, default=[])

    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User', back_populates='problems')
    # image_id = sqlalchemy.Column(sqlalchemy.Integer)
    comments = orm.relation("Comment", back_populates='problem')

    solutions = orm.relation("Solution", back_populates='problem')

    liked_by = sqlalchemy.Column(sqlalchemy.PickleType, default=[])
    are_interested = sqlalchemy.Column(sqlalchemy.PickleType, default=[])

    files = orm.relation("UsersFile", back_populates='problem')

    categories = orm.relation("Category",
                              secondary="problems_and_cats",
                              back_populates="problems")

    def get_rank(self):
        return int(self.rank * 1000) / 1000

    def get_needed_cats(self): # Получаем нужные категории
        res = []
        res.extend(get_categories_from_text(self.content))
        for comment in self.comments:
            res.extend(get_categories_from_text(comment.content))
        for solution in self.solutions:
            res.extend(get_categories_from_text(solution.content))
        return res
