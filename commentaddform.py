from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, MultipleFileField, BooleanField
from wtforms.validators import DataRequired


class CommentAddForm(FlaskForm):
    content = TextAreaField('Добавьте комментарий', validators=[DataRequired()])
    images = MultipleFileField('Добавьте картинки')
    delete_old_images = BooleanField("Удалить старые картинки")
    submit = SubmitField('Отправить')
