from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class ProblemEditForm(FlaskForm):
    content = TextAreaField("Условие",validators=[DataRequired()])
    submit = SubmitField('Применить')