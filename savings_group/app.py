import os
from http.cookiejar import month
from datetime import timedelta
import pandas as pd
from io import BytesIO

from flask import Flask, render_template, redirect, url_for, flash, session, request, send_file
from models import db, Member, Contribution, User
from forms import RegistrationForm, ContributionForm
from data import get_total_members, get_total_accounts, get_list_of_contributions, get_total_contributions,get_list_of_members, get_recent_contributions


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///savings_group.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret_key')
app.permanent_session_lifetime = timedelta(minutes=3)
db.init_app(app)

from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



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
            nber_of_accounts=form.nber_of_accounts.data
        )
        db.session.add(new_member)
        db.session.commit()
        flash(f'Member {form.first_name.data} registered successfully!', 'success')
        return redirect(url_for('register'))
    return render_template('register.html',
                           members=get_list_of_members(),
                           form=form)


@app.route('/contribute', methods=['GET', 'POST'])
@login_required
def contribute():
    form = ContributionForm()

    # Populate the dropdown with member IDs and names
    form.member.choices = [
        (member.id, f"{member.id} - {member.first_name} {member.last_name}")
        for member in Member.query.all()
    ]

    contribution_type= ['In Full', 'In Part']

    form.month.choices = [
        ('2024-01', 'January 2024'),
        ('2024-02', 'February 2024'),
        ('2024-03', 'March 2024'),
        ('2024-04', 'April 2024'),
        ('2024-05', 'May 2024'),
        ('2024-06', 'June 2024'),
        ('2024-07', 'July 2024'),
        ('2024-08', 'August 2024'),
        ('2024-09', 'September 2024'),
        ('2024-10', 'October 2024'),
        ('2024-11', 'November 2024'),
        ('2024-12', 'December 2024')
    ]

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
        # monthly_rate = 15500
        # daily_contr = 500
        # monthly_contr = 10000
        # social_contr = 2000
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



@app.route('/update_contributions', methods=['GET', 'POST'])
@login_required
def update_contributions():



    return render_template('update_contributions.html')




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




# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
