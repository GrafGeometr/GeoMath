from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField,BooleanField
from wtforms.validators import DataRequired


class ResetEmailForm(FlaskForm):
    password = PasswordField('Пароль',validators=[DataRequired()])
    email = EmailField('Новая почта', validators=[DataRequired()])
    email_again = EmailField('Повторите почту', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')
