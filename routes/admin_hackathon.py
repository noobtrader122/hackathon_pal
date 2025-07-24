from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from models.sqlalchemy_models import db, Hackathon, Challenge

admin_hackathon_bp = Blueprint('admin_hackathon', __name__, url_prefix='/admin/hackathon')

@admin_hackathon_bp.route('/new', methods=['GET', 'POST'])
def create_hackathon():
    challenges = Challenge.query.order_by(Challenge.title.asc()).all()
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        challenge_ids = request.form.getlist('challenge_ids')

        try:
            start_dt = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
            end_dt   = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')
        except Exception:
            flash("Invalid date/time format.", "error")
            return render_template("admin/new_hackathon.html", challenges=challenges)
        
        hackathon = Hackathon(
            name=name,
            description=description,
            start_time=start_dt,
            end_time=end_dt
        )
        db.session.add(hackathon)
        db.session.flush()  # So hackathon.id is available

        # Assign challenges
        for cid in challenge_ids:
            challenge = Challenge.query.get(int(cid))
            challenge.hackathon_id = hackathon.id
            db.session.add(challenge)

        db.session.commit()
        flash("Hackathon created!", "success")
        return redirect(url_for("admin_hackathon.create_hackathon"))
    return render_template("admin/new_hackathon.html", challenges=challenges)
