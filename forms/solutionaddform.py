from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, MultipleFileField, BooleanField, SelectField
from wtforms.validators import DataRequired


class SolutionAddForm(FlaskForm):
    content = TextAreaField('Добавьте ваше решение', validators=[DataRequired()])
    # latex = SelectField(choices=[(0, 'Обычный текст'), (1, 'LaTeX с автодополнением'), (2, 'LaTeX без автодополнения')])
    latex = SelectField(choices=[(0, 'Обычный текст'), (1, 'LaTeX с автодополнением')])
    images = MultipleFileField('Добавьте файлы')
    submit = SubmitField('Готово')
