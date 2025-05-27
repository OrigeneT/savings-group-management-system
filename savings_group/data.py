from savings_group.models import db, Member, Contribution
from sqlalchemy.sql import func
from sqlalchemy import text
from datetime import datetime

def get_list_of_members():
    return db.session.execute(text("SELECT id, first_name, last_name, phone, nber_of_accounts, strftime('%Y-%m-%d %H:%M', date_of_registration) AS date_of_registration, joining_date, next_of_kin FROM Member"))
    # return db.session.execute(text("SELECT * FROM Member"))

def get_list_of_contributions():
    return db.session.execute(text("""
        SELECT Contribution.*, Member.first_name, Member.last_name
        FROM Contribution
        JOIN Member ON Contribution.member_id = Member.id
        ORDER BY Contribution.month DESC
    """))

def get_total_members():
    return db.session.query(func.count(Member.id)).scalar()

def get_total_accounts():
    return db.session.query(func.sum(Member.nber_of_accounts)).scalar() or 0

def get_total_contributions():
    return db.session.query(func.sum(Contribution.daily_contr_amount) + func.sum(Contribution.monthly_contr_amount) + func.sum(Contribution.social_contr_amount)).scalar() or 0

def get_recent_contributions(limit=5):
    return Contribution.query.order_by(Contribution.date_contributed.desc()).limit(limit).all()


def get_all_months(start_year=2022):
    now = datetime.now()
    months = []
    for year in range(start_year, now.year + 1):
        last_month = now.month if year == now.year else 12
        for month in range(1, last_month + 1):
            value = f"{year}-{month:02d}"
            label = datetime(year, month, 1).strftime("%B %Y")
            months.append((value, label))
    return months[::-1]  # Most recent first


def get_available_months_for_member(member_id):
    all_months = get_all_months()
    contributed_months = {
        c.month for c in Contribution.query.filter_by(member_id=member_id).all()
    }
    return [m for m in all_months if m[0] not in contributed_months]