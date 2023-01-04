from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, MultipleFileField, BooleanField
from wtforms.validators import DataRequired


class CommentAddForm(FlaskForm):
    content = TextAreaField('Добавьте комментарий', validators=[DataRequired()])
    images = MultipleFileField('Добавьте файлы')
    submit = SubmitField('Готово')
