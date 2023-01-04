from flask_wtf import FlaskForm
from wtforms import FileField,SubmitField,StringField



class FileAddForm(FlaskForm):
    file = FileField('файл')
    geogebra_link = StringField('ссылка на чертёж в GeoGebra')
    submit = SubmitField('Добавить')