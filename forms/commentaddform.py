from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, MultipleFileField, SelectField
from wtforms.validators import DataRequired


class CommentAddForm(FlaskForm):
    content = TextAreaField('Добавьте комментарий', validators=[DataRequired()])
    # latex = SelectField(choices=[(0, 'Обычный текст'), (1, 'LaTeX с автодополнением'), (2, 'LaTeX без автодополнения')])
    latex = SelectField(choices=[(0, 'Обычный текст'), (1, 'LaTeX с автодополнением')])
    images = MultipleFileField('Добавьте файлы')
    submit = SubmitField('Готово')
