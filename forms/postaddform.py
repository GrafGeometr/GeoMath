from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms import BooleanField, SubmitField,MultipleFileField
from wtforms.validators import DataRequired


class PostAddForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    theme = SelectField(choices=[(0, 'Геометрия'), (1, 'Алгебра и ТЧ'), (2, 'Комбинаторика')])
    content = TextAreaField("Содержание")
    submit = SubmitField('Готово')