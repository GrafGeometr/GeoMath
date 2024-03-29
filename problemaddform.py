from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms import BooleanField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired


class ProblemAddForm(FlaskForm):
    content = TextAreaField("Условие", validators=[DataRequired()])
    images = MultipleFileField('Добавьте файлы')
    theme = SelectField(choices=[(0, 'Геометрия'), (1, 'Алгебра и ТЧ'), (2, 'Комбинаторика')])
    notauthor = BooleanField("Выберите, если вы не являетесь автором задачи")
    original_solution = TextAreaField("Авторское решение")
    solution_images = MultipleFileField('Добавьте файлы к решению')
    nosolution = BooleanField("Нет решения")
    submit = SubmitField('Готово')
