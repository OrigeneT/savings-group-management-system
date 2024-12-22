import os
from flask import Flask, render_template, redirect, url_for, flash
from models import db, Member, Contribution
from forms import RegistrationForm, ContributionForm
from data import get_total_members, get_total_accounts, get_total_contributions,get_list_of_members, get_recent_contributions


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///savings_group.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret_key')
db.init_app(app)


@app.route('/')
@app.route('/home')
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
def contribute():
    form = ContributionForm()

    # Populate the dropdown with member IDs and names
    form.member.choices = [
        (member.id, f"{member.id} - {member.first_name} {member.last_name}")
        for member in Member.query.all()
    ]

    if form.validate_on_submit():
        member_id = form.member.data
        member = Member.query.filter_by(id=member_id).first()

        # Calculate the contribution amount
        monthly_rate = 15500
        total_contribution = monthly_rate * member.nber_of_accounts

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
            month=form.month.data,
            amount=total_contribution
        )
        db.session.add(new_contribution)
        db.session.commit()
        flash(f'Contribution of {total_contribution} recorded for {member.first_name} {member.last_name}!', 'success')
        return redirect(url_for('contribute'))

    return render_template('contribute.html', form=form)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
