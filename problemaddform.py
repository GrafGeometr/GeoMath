from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class ProblemAddForm(FlaskForm):
    content = TextAreaField("Условие",validators=[DataRequired()])
    original_solution = TextAreaField("Авторское решение")
    nosolution = BooleanField("Нет решения")
    submit = SubmitField('Применить')