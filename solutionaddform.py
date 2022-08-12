from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, MultipleFileField, BooleanField
from wtforms.validators import DataRequired


class SolutionAddForm(FlaskForm):
    content = TextAreaField('Добавьте ваше решение', validators=[DataRequired()])
    images = MultipleFileField('Добавьте файлы')
    submit = SubmitField('Отправить')
