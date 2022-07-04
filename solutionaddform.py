from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, MultipleFileField, BooleanField
from wtforms.validators import DataRequired


class SolutionAddForm(FlaskForm):
    content = TextAreaField('Добавьте ваше решение', validators=[DataRequired()])
    images = MultipleFileField('Добавьте картинки')
    delete_old_images = BooleanField("Удалить старые картинки")
    submit = SubmitField('Отправить')
