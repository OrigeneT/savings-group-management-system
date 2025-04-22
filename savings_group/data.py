from models import db, Member, Contribution
from sqlalchemy.sql import func
from sqlalchemy import text

def get_list_of_members():
    return db.session.execute(text("SELECT id, first_name, last_name, phone, nber_of_accounts, strftime('%Y-%m-%d %H:%M', date_of_registration) AS date FROM Member"))
    # data = db.session.execute(text("SELECT * FROM Member"))
    # print(data.columns)
    # return data.columns
def get_list_of_contributions():
    return db.session.execute(text("SELECT * FROM Contribution"))

def get_total_members():
    return db.session.query(func.count(Member.id)).scalar()

def get_total_accounts():
    return db.session.query(func.sum(Member.nber_of_accounts)).scalar() or 0

def get_total_contributions():
    return db.session.query(func.sum(Contribution.daily_contr_amount) + func.sum(Contribution.monthly_contr_amount) + func.sum(Contribution.social_contr_amount)).scalar() or 0

def get_recent_contributions(limit=5):
    return Contribution.query.order_by(Contribution.date_contributed.desc()).limit(limit).all()
