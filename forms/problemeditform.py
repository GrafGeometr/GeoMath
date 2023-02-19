from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms import BooleanField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired


class ProblemEditForm(FlaskForm):
    content = TextAreaField("Условие", validators=[DataRequired()])
    theme = SelectField(choices=[(0, 'Геометрия'), (1, 'Алгебра и ТЧ'), (2, 'Комбинаторика')])
    # latex = SelectField(choices=[(0, 'Обычный текст'), (1, 'LaTeX с автодополнением'), (2, 'LaTeX без автодополнения')])
    latex = SelectField(choices=[(0, 'Обычный текст'), (1, 'LaTeX с автодополнением')])
    notauthor = BooleanField("Выберите, если вы не являетесь автором задачи")
    images = MultipleFileField('Добавьте файлы')
    submit = SubmitField('Применить')
