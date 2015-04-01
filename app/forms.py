from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, FloatField
from wtforms.validators import DataRequired, NumberRange

class LoginForm(Form):
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class SettingsForm(Form):
    commute_tag = BooleanField('commute_tag', default=False)
    commute_string = StringField('commute_string')
    goal_string = StringField('goal_string')
    goal_number = FloatField('goal_number', validators=[NumberRange(1,999999)])
    savings = FloatField('savings', validators=[NumberRange(1,999)])