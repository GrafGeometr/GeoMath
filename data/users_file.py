import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class UsersFile(SqlAlchemyBase):
    __tablename__ = 'users_files'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)

    extension = sqlalchemy.Column(sqlalchemy.String)

    post_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("posts.id"))
    post = orm.relation('Post')
    problem_id = sqlalchemy.Column(sqlalchemy.Integer,
                                   sqlalchemy.ForeignKey("problems.id"))
    problem = orm.relation('Problem')
    solution_id = sqlalchemy.Column(sqlalchemy.Integer,
                                    sqlalchemy.ForeignKey("solutions.id"))
    solution = orm.relation('Solution')
    comment_id = sqlalchemy.Column(sqlalchemy.Integer,
                                   sqlalchemy.ForeignKey("comments.id"))
    comment = orm.relation('Comment')
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                   sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User')

    def __repr__(self):
        if self.extension=='.ggb':
            return f'<iframe  scrolling="no" src="{self.name}" width="1100px" height="1000px" style="border:0px;"></iframe><br>'
        if self.extension in ['.txt', '.pdf', '.doc', '.docx']:
            return f'<a class="btn btn-primary" target="_blank" href="/static/user_files/{self.id}{self.extension}">{self.name}</a><br>'
        elif self.extension in ['.png', '.jpeg', '.jpg', '.gif']:
            return f'<img src="/static/user_files/{self.id}{self.extension}" height="400"><br>'

    def edit(self, togo):
        if self.extension=='.ggb':
            return f'<iframe  scrolling="no" src="{self.name}" width="900px" height="700px" style="border:0px;"></iframe><a href="/delete_file/{self.id}/{togo}" class="btn btn-danger">Удалить</a><br>'
        if self.extension in ['.txt', '.pdf', '.doc', '.docx']:
            return f'<a class="btn btn-primary" target="_blank" href="/static/user_files/{self.id}{self.extension}">{self.name}</a><a href="/delete_file/{self.id}/{togo}" class="btn btn-danger">Удалить</a><br>'
        elif self.extension in ['.png', '.jpeg', '.jpg', '.gif']:
            return f'<img src="/static/user_files/{self.id}{self.extension}" height="50"><a href="/delete_file/{self.id}/{togo}" class="btn btn-danger">Удалить</a><br>'
