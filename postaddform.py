from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms import BooleanField, SubmitField,MultipleFileField
from wtforms.validators import DataRequired


class PostAddForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    images = MultipleFileField('Добавьте картинки')
    content = TextAreaField("Содержание")
    delete_old_images = BooleanField("Удалить старые картинки")
    submit = SubmitField('Применить')