from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms import BooleanField, SubmitField,MultipleFileField
from wtforms.validators import DataRequired


class AdminForm(FlaskForm):
    content = TextAreaField("Сообщение от администраторов")
    submit = SubmitField('Готово')