from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Regexp, NumberRange

class RegistrationForm(FlaskForm):
    member_id = StringField(
        'Member ID',
        validators=[
            DataRequired(),
            Length(min=16, max=16, message="National ID must be 16 digits"),
            Regexp(r'^119\d{13}$', message="National ID must start with '119'")
        ]
    )
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    phone = StringField('Phone',
                    validators=[DataRequired(),
                    Length(min=10, max=10, message="Phone Number must be 10 digits"),
                    Regexp(r'^07\d{8}$', message="Phone Number must start with '07' only contain numbers")
                                ])
    nber_of_accounts = IntegerField('Number of accounts', validators=[DataRequired(), NumberRange(min=0, max=10)])
    submit = SubmitField('Register')


class ContributionForm(FlaskForm):
    member = SelectField('Select Member', coerce=str, validators=[DataRequired()])
    month = StringField(
        'Month (YYYY-MM)',
        validators=[DataRequired(), Regexp(r'^\d{4}-\d{2}$', message="Invalid month format (YYYY-MM)")]
    )
    submit = SubmitField('Record Contribution')