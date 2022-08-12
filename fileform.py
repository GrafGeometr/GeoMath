from flask_wtf import FlaskForm
from wtforms import FileField,SubmitField



class FileAddForm(FlaskForm):
    file = FileField('Добавьте файл')
    submit = SubmitField('Добавить')