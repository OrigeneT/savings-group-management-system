import os
from http.cookiejar import month
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta
import pandas as pd
from io import BytesIO

from flask import Flask, render_template, redirect, url_for, flash, session, request, send_file, jsonify
from flask_migrate import Migrate
from savings_group.models import db, Member, Contribution, User, ContributionHistory, MemberHistory, Loan, LoanRepayment
from savings_group.forms import RegistrationForm, ContributionForm, LoanForm, LoanRepaymentForm
from savings_group.data import get_total_members, get_total_accounts, get_list_of_contributions, get_total_contributions,get_list_of_members, get_recent_contributions, get_available_months_for_member, get_all_months


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///savings_group.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret_key')
app.permanent_session_lifetime = timedelta(minutes=10)
db.init_app(app)
migrate = Migrate(app, db)

from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



# @app.route('/create_admin')
# def create_admin():
#     if not User.query.filter_by(username='admin').first():
#         admin = User(username='admin')
#         admin.set_password('admin123')  # Make sure set_password hashes the password
#         db.session.add(admin)
#         db.session.commit()
#         return "Admin user created!"
#     return "Admin user already exists!"



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session.permanent = True  # this enables the timeout
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
            # return redirect(url_for('dashboard'))  # or any protected route
        else:
            flash("Invalid username or password")
    return render_template('login.html')


@app.route('/')
@app.route('/home')
@login_required
def home():
    metrics = {
        "total_members": get_total_members(),
        "total_accounts": get_total_accounts(),
        "total_contributions": get_total_contributions()
    }

    return render_template('index.html',
                           metrics=metrics,
                           members =get_list_of_members())


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_member = Member.query.filter_by(id=form.member_id.data).first()
        if existing_member:
            flash(f'Member ID {form.member_id.data} already exists!', 'danger')
            return redirect(url_for('register'))

        new_member = Member(
            id=form.member_id.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            nber_of_accounts=form.nber_of_accounts.data,
            joining_date=form.joining_date.data,
            next_of_kin=form.next_of_kin.data
        )
        db.session.add(new_member)
        db.session.commit()
        flash(f'Member {form.first_name.data} registered successfully!', 'success')
        return redirect(url_for('register'))
    members = get_list_of_members()
    return render_template('register.html', form=form, members=members, now=datetime.now)



@app.route('/edit_member/<member_id>', methods=['GET', 'POST'])
@login_required
def edit_member(member_id):
    member = Member.query.get_or_404(member_id)
    form = RegistrationForm(obj=member)
    form.member_id.data = member.id # Manually setting the member_id field with value
    if form.validate_on_submit():
        form.populate_obj(member)
        db.session.commit()
        flash("Member's details updated successfully!", 'success')
        return redirect(url_for('register'))
    return render_template('edit_member.html', form=form, member=member)





@app.route('/contribute', methods=['GET', 'POST'])
@login_required
def contribute():
    form = ContributionForm()
    # Populate the dropdown with member IDs and names
    form.member.choices = [
        (str(member.id), f"{member.id} - {member.first_name} {member.last_name}")
        for member in Member.query.all()
    ]



    # form.month.choices = [
    #     ('2024-01', 'January 2024'),
    #     ('2024-02', 'February 2024'),
    #     ('2024-03', 'March 2024'),
    #     ('2024-04', 'April 2024'),
    #     ('2024-05', 'May 2024'),
    #     ('2024-06', 'June 2024'),
    #     ('2024-07', 'July 2024'),
    #     ('2024-08', 'August 2024'),
    #     ('2024-09', 'September 2024'),
    #     ('2024-10', 'October 2024'),
    #     ('2024-11', 'November 2024'),
    #     ('2024-12', 'December 2024')
    # ]
    # Default: show all months if no member selected yet
    selected_member_id = form.member.data or (form.member.choices[0][0] if form.member.choices else None)
    if selected_member_id:
        form.month.choices = get_available_months_for_member(selected_member_id)
    else:
        form.month.choices = get_all_months()



    form.contrib_type.choices = [
        ('In Full', 'In Full'),
        ('Partial', 'Partial')
    ]

    form.contrib_time.choices = [
        ('On Time', 'On Time'),
        ('Late', 'Late')
    ]


    if form.validate_on_submit():
        member_id = form.member.data
        member = Member.query.filter_by(id=member_id).first()
        month = form.month.data
        contrib_type = form.contrib_type.data
        contrib_time = form.contrib_time.data
        daily_contr_amount = form.daily_contr_amount.data
        monthly_contr_amount = form.monthly_contr_amount.data
        social_contr_amount = form.social_contr_amount.data
        late_days   = form.late_days.data
        comment = form.comment.data or ""  # Default to empty string
        # Calculate the contribution amount
        penalty_amount = form.penalty_amount.data or 0  # Default to 0 if None
        total_paid = (daily_contr_amount or 0) + (monthly_contr_amount or 0) + (
                    social_contr_amount or 0) + penalty_amount

        # Check if contribution for this month already exists
        existing_contribution = Contribution.query.filter_by(
            member_id=member.id, month=form.month.data
        ).first()
        if existing_contribution:
            flash(f'Contribution for {form.month.data} already recorded!', 'warning')
            return redirect(url_for('contribute'))

        # Record the contribution
        new_contribution = Contribution(
            member_id=member.id,
            month=month,
            contrib_type =contrib_type,
            contrib_time =contrib_time,
            daily_contr_amount = daily_contr_amount,
            monthly_contr_amount = monthly_contr_amount,
            social_contr_amount = social_contr_amount,
            late_days = late_days,
            penalty_amount = penalty_amount,
            total_paid=total_paid,
            comment=comment
        )
        print("Form Submitted Data:", form.data)

        db.session.add(new_contribution)
        db.session.commit()
        flash(f'Contribution of {total_paid} recorded for {member.first_name} {member.last_name}!', 'success')
        return redirect(url_for('contribute'))
    else:
        print("Form Errors:", form.errors)

    return render_template('contribute.html', form=form, contributions =get_list_of_contributions())



@app.route('/edit_contribution/<int:contribution_id>', methods=['GET', 'POST'])
@login_required
def edit_contribution(contribution_id):
    contribution = Contribution.query.get_or_404(contribution_id)
    form = ContributionForm()
    form.member.choices = [(str(contribution.member_id), f"{contribution.member_id} - {contribution.member.first_name} {contribution.member.last_name}")]

    try:
        year, month_num = map(int, contribution.month.split('-'))
        label = datetime(year, month_num, 1).strftime("%B %Y")
    except Exception:
        label = contribution.month
    form.month.choices = [(contribution.month, label)]

    form.contrib_type.choices = [
        ('In Full', 'In Full'),
        ('Partial', 'Partial')
    ]
    form.contrib_time.choices = [
        ('On Time', 'On Time'),
        ('Late', 'Late')
    ]

    if request.method == 'GET':
        form.process(obj=contribution)


    if form.validate_on_submit():
        contribution.member_id = form.member.data  # This should be the ID, not the relationship
        contribution.month = form.month.data
        contribution.contrib_type = form.contrib_type.data
        contribution.contrib_time = form.contrib_time.data
        contribution.daily_contr_amount = form.daily_contr_amount.data
        contribution.monthly_contr_amount = form.monthly_contr_amount.data
        contribution.social_contr_amount = form.social_contr_amount.data
        contribution.late_days = form.late_days.data
        contribution.penalty_amount = form.penalty_amount.data
        contribution.total_paid = (
            (form.daily_contr_amount.data or 0)
            + (form.monthly_contr_amount.data or 0)
            + (form.social_contr_amount.data or 0)
            + (form.penalty_amount.data or 0)
        )
        contribution.comment = form.comment.data

        db.session.commit()
        flash("Contribution updated successfully!", "success")
        return redirect(url_for('contribute'))
    return render_template('edit_contribution.html', form=form, contribution=contribution)


@app.route('/delete_member/<member_id>', methods=['POST'])
@login_required
def delete_member(member_id):
    member = Member.query.get_or_404(member_id)
    contributions = Contribution.query.filter_by(member_id=member.id).all()

    # Archive contributions
    for c in contributions:
        history = ContributionHistory(
            # Copy all fields from c
            member_id=c.member_id,
            month=c.month,
            contrib_type=c.contrib_type,
            contrib_time=c.contrib_time,
            daily_contr_amount=c.daily_contr_amount,
            monthly_contr_amount=c.monthly_contr_amount,
            social_contr_amount=c.social_contr_amount,
            late_days=c.late_days,
            penalty_amount=c.penalty_amount,
            total_paid=c.total_paid,
            comment=c.comment,
            deleted_at=datetime.utcnow()
        )
        db.session.add(history)
        db.session.delete(c)

    # Archive member
    member_history = MemberHistory(
        id=member.id,
        first_name=member.first_name,
        last_name=member.last_name,
        phone=member.phone,
        nber_of_accounts=member.nber_of_accounts,
        joining_date=member.joining_date,
        next_of_kin=member.next_of_kin,
        date_of_registration=member.date_of_registration,
        deleted_at=datetime.utcnow()
    )
    db.session.add(member_history)
    db.session.delete(member)

    db.session.commit()
    flash('Member and their contributions archived and deleted!', 'success')
    return redirect(url_for('register'))


@app.route('/delete_contribution/<int:contribution_id>', methods=['POST'])
@login_required
def delete_contribution(contribution_id):
    contribution = Contribution.query.get_or_404(contribution_id)
    db.session.delete(contribution)
    db.session.commit()
    flash("Contribution deleted successfully!", "success")
    return redirect(url_for('contribute'))



@app.route('/loans', methods=['GET', 'POST'])
@login_required
def loans():
    form = LoanForm()
    form.member.choices = [
        (str(m.id), f"{m.id} - {m.first_name} {m.last_name}") for m in Member.query.all()
    ]

    selected_member_id = form.member.data or (form.member.choices[0][0] if form.member.choices else None)
    max_loan = 0
    if selected_member_id:
        year = datetime.now().year
        max_loan = db.session.query(
            db.func.sum(Contribution.total_paid)
        ).filter(
            Contribution.member_id == selected_member_id,
            db.func.substr(Contribution.month, 1, 4) == str(year)
        ).scalar() or 0





    if form.validate_on_submit():

        principal = form.amount.data
        months = form.repayment_period_months.data
        monthly_interest = principal * 0.05
        expected_monthly_payment = principal / months
        total_repayment = (expected_monthly_payment + monthly_interest) * months

        # Compute deadline
        first_repayment = form.first_repayment_date.data
        deadline = first_repayment + relativedelta(months=months)
        # Check deadline

        if deadline > date(datetime.now().year, 12, 31):
            flash("Loan have to be fully paid before the end of the current year.", "danger")
        else:
            loan = Loan(
                member_id=form.member.data,
                amount=principal,
                repayment_period_months=months,
                first_repayment_date=form.first_repayment_date.data,  # if you use this field
                monthly_interest_rate=0.05,
                late_interest_rate=0.10,
                total_repayment_amount=total_repayment,
                expected_monthly_payment=expected_monthly_payment,
                monthly_interest_amount=monthly_interest,
                deadline=deadline,
                status=form.status.data
            )
            db.session.add(loan)
            db.session.commit()
            flash("Loan recorded successfully!", "success")
            return redirect(url_for('loans'))
    
    else:
        print("Loan form errors:", form.errors)
    loans = Loan.query.all()
    return render_template('loans.html', form=form, loans=loans, max_loan=max_loan)



@app.route('/loan_repayment', methods=['GET', 'POST'])
@login_required
def loan_repayment():
    form = LoanRepaymentForm()
    form.loan.choices = [
        (l.id, f"{l.member_id} - {l.amount} ({l.status})") for l in Loan.query.filter(Loan.status != 'Fully paid').all()
    ]
    if form.validate_on_submit():
        loan = Loan.query.get(form.loan.data)
        interest = 0.10 if form.is_late.data else 0.05
        repayment_amount = form.amount.data * (1 + (interest if form.is_late.data else 0))
        repayment = LoanRepayment(
            loan_id=loan.id,
            amount=repayment_amount,
            is_late=form.is_late.data,
            interest_applied=interest
        )
        db.session.add(repayment)
        # Update loan status if fully paid
        total_repaid = sum(r.amount for r in loan.repayments) + repayment_amount
        if total_repaid >= loan.total_repayment_amount:
            loan.status = 'Fully paid'
        else:
            loan.status = 'Under repayment'
        db.session.commit()
        flash("Repayment recorded!", "success")
        return redirect(url_for('loan_repayment'))
    repayments = LoanRepayment.query.all()
    return render_template('loan_repayment.html', form=form, repayments=repayments)





@app.route('/get_max_loan/<member_id>')
@login_required
def get_max_loan(member_id):
    year = datetime.now().year
    max_loan = db.session.query(
        db.func.sum(Contribution.daily_contr_amount + Contribution.monthly_contr_amount)
    ).filter(
        Contribution.member_id == member_id,
        db.func.substr(Contribution.month, 1, 4) == str(year)
    ).scalar() or 0
    return jsonify({'max_loan': max_loan})






@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



@app.route('/download_list_of_members', methods=['GET', 'POST'])
@login_required
def download_list_of_members():
    df = get_list_of_members()
    list_of_members = pd.DataFrame(df.fetchall(), columns=df.keys())

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        list_of_members.to_excel(writer, index=False, sheet_name='Members')
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        download_name="Ubumwe group members.xlsx",
        as_attachment=True
    )

@app.route('/download_list_of_contributions', methods=['GET', 'POST'])
@login_required
def download_list_of_contributions():
    df = get_list_of_contributions()
    list_of_contributions = pd.DataFrame(df.fetchall(), columns=df.keys())

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        list_of_contributions.to_excel(writer, index=False, sheet_name='Contributions')
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        download_name="Ubumwe group contributions.xlsx",
        as_attachment=True
    )

@app.route('/get_available_months/<member_id>')
@login_required
def get_available_months(member_id):
    months = get_available_months_for_member(member_id)
    # months is a list of tuples: [(value, label), ...]
    return jsonify(months)

# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)

# with app.app_context():
#     db.create_all()

# if __name__ == '__main__':
#     app.run(debug=True)
