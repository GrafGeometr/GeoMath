from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField
from wtforms.validators import DataRequired


class VerifyForm(FlaskForm):
    code = PasswordField('Введите код, который мы отправили вам на электронную почту')
    submit = SubmitField('Проверить код')
    # repeat = SubmitField('Выслать код повторно')