from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
import pytz
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Define GMT+2 timezone
gmt_plus_2 = pytz.timezone('Africa/Johannesburg')

class Member(db.Model):
    id = db.Column(db.String(16), primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(10), nullable=False)
    nber_of_accounts = db.Column(db.Integer, nullable=False)
    joining_date = db.Column(db.Date, nullable=True)
    next_of_kin = db.Column(db.String(100), nullable=True) 
    date_of_registration = db.Column(
        db.DateTime,
        default=lambda: datetime.now(gmt_plus_2).replace(second=0, microsecond=0),
        nullable=False
    )



class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String(16), db.ForeignKey('member.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # Format: YYYY-MM
    contrib_type = db.Column(db.String(7), nullable=False) #Either In full and In part
    contrib_time = db.Column(db.String(7), nullable=False)  # Either In full and In part
    daily_contr_amount = db.Column(db.Float, nullable=False) #Daily Contribution
    monthly_contr_amount = db.Column(db.Float, nullable=False) #Monthly Contribution
    social_contr_amount = db.Column(db.Float, nullable=False) #Social Contribution
    date_of_record_reg = db.Column(db.DateTime, default=lambda: datetime.now(gmt_plus_2).replace(microsecond=0), nullable=False)
    late_days = db.Column(db.Integer, nullable=True) #Number of Days the contribution has been late
    penalty_amount = db.Column(db.Float, nullable=True)  # Total penalties paid
    total_paid = db.Column(db.Float, nullable=True)  # Total amount paid (contributions + penalties)
    comment = db.Column(db.String(400), nullable=True) # Any comment the user want to put in
    member = db.relationship('Member', backref=db.backref('contributions', lazy=True))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')  # e.g. 'admin', 'user'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    



class MemberHistory(db.Model):
    __tablename__ = 'member_history'
    id = db.Column(db.String, primary_key=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    phone = db.Column(db.String)
    nber_of_accounts = db.Column(db.Integer)
    joining_date = db.Column(db.Date)
    next_of_kin = db.Column(db.String)
    date_of_registration = db.Column(db.DateTime)
    deleted_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContributionHistory(db.Model):
    __tablename__ = 'contribution_history'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String)
    month = db.Column(db.String)
    contrib_type = db.Column(db.String)  
    contrib_time = db.Column(db.String)
    daily_contr_amount = db.Column(db.Integer)
    monthly_contr_amount = db.Column(db.Integer)
    social_contr_amount = db.Column(db.Integer)
    late_days = db.Column(db.Integer)
    penalty_amount = db.Column(db.Integer)
    total_paid = db.Column(db.Integer)
    comment = db.Column(db.String)
    deleted_at = db.Column(db.DateTime)



class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String, db.ForeignKey('member.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    repayment_period_months = db.Column(db.Integer, nullable=False)
    first_repayment_date = db.Column(db.Date, nullable=False)  # NEW
    monthly_interest_rate = db.Column(db.Float, nullable=False, default=0.05)
    late_interest_rate = db.Column(db.Float, nullable=False, default=0.10)
    total_repayment_amount = db.Column(db.Float, nullable=False)
    expected_monthly_payment = db.Column(db.Float, nullable=False)  # NEW
    monthly_interest_amount = db.Column(db.Float, nullable=False)   # NEW
    deadline = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32), nullable=False, default='Requested')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    repayments = db.relationship('LoanRepayment', backref='loan', lazy=True)

class LoanRepayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_late = db.Column(db.Boolean, nullable=False, default=False)
    interest_applied = db.Column(db.Float, nullable=False, default=0.05)