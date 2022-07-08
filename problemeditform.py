from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms import BooleanField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired


class ProblemEditForm(FlaskForm):
    content = TextAreaField("Условие", validators=[DataRequired()])
    theme = SelectField(choices=[(0, 'Геометрия'), (1, 'Алгебра и ТЧ'), (2, 'Комбинаторика')])
    images = MultipleFileField('Добавьте картинку(и)')
    delete_old_images = BooleanField("Удалить старые картинки")
    submit = SubmitField('Применить')
