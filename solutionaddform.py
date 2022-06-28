from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired


class SolutionAddForm(FlaskForm):
    content = TextAreaField('Добавьте ваше решение', validators=[DataRequired()])
    submit = SubmitField('Отправить')
