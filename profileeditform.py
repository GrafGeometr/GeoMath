from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField,BooleanField
from wtforms.validators import DataRequired


class ProfileEditForm(FlaskForm):
    secret_code = StringField("Код идентификации для изменения статуса")
    change_status = BooleanField("Изменить статус")
    email = EmailField('Почта', validators=[DataRequired()])
    old_password = PasswordField('Старый пароль', validators=[DataRequired()])
    password = PasswordField("Новый пароль", validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    about = TextAreaField("Немного о себе")
    submit = SubmitField('Войти')
