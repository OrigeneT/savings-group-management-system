from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, DateField, FloatField, BooleanField
from wtforms.validators import DataRequired, Length, Regexp, NumberRange, Optional

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
                    Regexp(r'^07\d{8}$', message="Phone Number must start with '07' and only contain numbers")
                                ])
    nber_of_accounts = IntegerField('Number of Accounts', validators=[DataRequired(), NumberRange(min=0, max=5)])
    joining_date = DateField('Joining Date', format='%Y-%m-%d', validators=[DataRequired()])
    next_of_kin = StringField('Next of Kin', validators=[DataRequired()])
    submit = SubmitField('Register')


class ContributionForm(FlaskForm):
    member = SelectField('Select Member', coerce=str, validators=[DataRequired()])
    month = SelectField(
        'Month',
        validators=[DataRequired(), Regexp(r'^\d{4}-\d{2}$', message="Invalid month format (YYYY-MM)")]
    )
    contrib_type =SelectField('Contribution level', validators=[DataRequired()])
    contrib_time =SelectField('Is contribution on Time', validators=[DataRequired()])
    daily_contr_amount = IntegerField('Daily Contribution', validators=[DataRequired()])
    monthly_contr_amount = IntegerField('Monthly Contribution', validators=[DataRequired()])
    social_contr_amount = IntegerField('Social Contribution', validators=[DataRequired()])
    late_days = IntegerField('Number of Late days', validators=[Optional(), NumberRange(min=0, max=100)])
    penalty_amount = IntegerField('Total Penalties', validators=[Optional()])
    comment = StringField('Comments (if any)', validators=[Optional()])
    submit = SubmitField('Save Contribution')



class LoanForm(FlaskForm):
    member = SelectField('Member', coerce=str, validators=[DataRequired()])
    amount = FloatField('Loan Amount', validators=[DataRequired(), NumberRange(min=1)])
    repayment_period_months = IntegerField('Payment Period (months)', validators=[DataRequired(), NumberRange(min=1, max=12)])
    first_repayment_date = DateField('First Repayment Date', validators=[DataRequired()])
    # monthly_installment_deadline = IntegerField('Monthly Installment Deadline (day of month)', validators=[DataRequired(), NumberRange(min=1, max=31)])
    # deadline = DateField('Final Repayment Deadline', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Approved', 'Approved'),
        ('Under_repayment', 'Under repayment'),
        ('Fully_paid', 'Fully paid')
    ], validators=[DataRequired()])
    submit = SubmitField('Record Loan')

class LoanRepaymentForm(FlaskForm):
    loan = SelectField('Loan', coerce=int, validators=[DataRequired()])
    amount = FloatField('Repayment Amount', validators=[DataRequired(), NumberRange(min=1)])
    is_late = BooleanField('Is Late?')
    submit = SubmitField('Record Repayment')