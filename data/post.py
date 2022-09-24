import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase

# Выделяем теги из текста
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

# Пост
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

    liked_by = sqlalchemy.Column(sqlalchemy.PickleType, default=[])

    files = orm.relation("UsersFile", back_populates='post')

    categories = orm.relation("Category",
                              secondary="posts_and_cats",
                              back_populates="posts")

    def get_rank(self):
        if self.rank<0:
            self.rank = 0
        return self.rank

    def get_needed_cats(self): # Получаем нужные категории
        res = []
        res.extend(get_categories_from_text(self.content))
        res.extend(get_categories_from_text(self.title))
        for comment in self.comments:
            res.extend(get_categories_from_text(comment.content))
        return res

