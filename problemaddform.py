from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms import BooleanField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired


class ProblemAddForm(FlaskForm):
    content = TextAreaField("Условие", validators=[DataRequired()])
    images = MultipleFileField('Добавьте картинку(и)')
    theme = SelectField(choices=[(0, 'Геометрия'), (1, 'Алгебра и ТЧ'), (2, 'Комбинаторика')])
    original_solution = TextAreaField("Авторское решение")
    solution_images = MultipleFileField('Добавьте картинки к решению')
    nosolution = BooleanField("Нет решения")
    submit = SubmitField('Применить')
