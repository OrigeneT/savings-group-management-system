from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
import pytz

db = SQLAlchemy()

# Define GMT+2 timezone
gmt_plus_2 = pytz.timezone('Africa/Johannesburg')

class Member(db.Model):
    id = db.Column(db.String(16), primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(10), nullable=False)
    nber_of_accounts = db.Column(db.Integer, nullable=False)
    date_of_registration = db.Column(
        db.DateTime,
        default=lambda: datetime.now(gmt_plus_2),
        nullable=False
    )



class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String(16), db.ForeignKey('member.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # Format: YYYY-MM
    amount = db.Column(db.Float, nullable=False)
    date_contributed = db.Column(db.Date, default=date.today)

    member = db.relationship('Member', backref=db.backref('contributions', lazy=True))