from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms import BooleanField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired


class NavForm(FlaskForm):
    geom = BooleanField("Геометрия", default=True)
    algb = BooleanField("Алгебра и ТЧ", default=True)
    comb = BooleanField("Комбинаторика", default=True)
    posts = BooleanField("Посты", default=True)
    solprob = BooleanField("Задачи с решениями", default=True)
    nosolprob = BooleanField("Задачи без решения", default=True)
    time = SelectField(choices=['30 минут', '5 часов', '1 день', 'неделя', 'месяц', 'год', 'всё время'],
                       default='30 минут')
    # keywords = StringField("Ключевые слова")
    submit = SubmitField('Искать')
