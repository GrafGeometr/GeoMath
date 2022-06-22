from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class PostForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    post_type = SelectField('Вид поста', choices=['лекция','задача','решение','замечание'])
    content = TextAreaField("Содержание")
    is_private = BooleanField("Личное")
    submit = SubmitField('Применить')