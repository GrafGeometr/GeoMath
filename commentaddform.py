from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired


class CommentAddForm(FlaskForm):
    content = TextAreaField('Добавьте комментарий', validators=[DataRequired()])
    submit = SubmitField('Отправить')
