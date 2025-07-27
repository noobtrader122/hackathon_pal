from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+ timezone management
from models.sqlalchemy_models import db, Hackathon, Challenge


admin_hackathon_bp = Blueprint('admin_hackathon', __name__, url_prefix='/admin/hackathon')


from datetime import datetime, timezone, timedelta

@admin_hackathon_bp.route("/")
def list_hackathons():
    hackathons = Hackathon.query.order_by(Hackathon.id).all()
    return render_template("index.html", hackathons=hackathons, now=datetime.now(timezone.utc), timedelta=timedelta)



@admin_hackathon_bp.route('/new', methods=['GET', 'POST'])
def create_hackathon():
    challenges = Challenge.query.order_by(Challenge.title.asc()).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        challenge_ids = request.form.getlist('challenge_ids')  # selected challenge ids

        tz_ist = ZoneInfo("Asia/Kolkata")  # Assuming form inputs are in IST timezone

        if not name:
            flash("Please provide a name for the hackathon.", "error")
            return render_template("admin/new_hackathon.html", challenges=challenges)

        try:
            start_dt_naive = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
            end_dt_naive = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')

            # Localize naive datetime to IST timezone-aware datetime
            start_dt_aware = start_dt_naive.replace(tzinfo=tz_ist)
            end_dt_aware = end_dt_naive.replace(tzinfo=tz_ist)

            # Convert to UTC datetime for consistent DB storage
            start_dt_utc = start_dt_aware.astimezone(ZoneInfo("UTC"))
            end_dt_utc = end_dt_aware.astimezone(ZoneInfo("UTC"))
        except Exception:
            flash("Invalid date/time format. Please use the correct format.", "error")
            return render_template("admin/new_hackathon.html", challenges=challenges)

        hackathon = Hackathon(
            name=name,
            description=description,
            start_time=start_dt_utc,
            end_time=end_dt_utc
        )
        db.session.add(hackathon)
        db.session.flush()  # To get hackathon.id before commit if needed

        # Convert challenge IDs to integers
        selected_ids = set(map(int, challenge_ids))

        # Select only those challenges that are chosen
        selected_challenges = [c for c in challenges if c.id in selected_ids]

        # Assign challenges to hackathon using many-to-many relationship
        hackathon.challenges = selected_challenges

        db.session.commit()
        flash("Hackathon created!", "success")
        return redirect(url_for("admin_hackathon.create_hackathon"))

    return render_template("admin/new_hackathon.html", challenges=challenges)


@admin_hackathon_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_hackathon(id):
    hackathon = Hackathon.query.get_or_404(id)
    challenges = Challenge.query.order_by(Challenge.title.asc()).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        challenge_ids = request.form.getlist('challenge_ids')

        tz_ist = ZoneInfo("Asia/Kolkata")  # Your timezone

        if not name:
            flash("Please provide a name for the hackathon.", "error")
            return render_template("admin/edit_hackathon.html", hackathon=hackathon, challenges=challenges)

        try:
            start_dt_naive = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
            end_dt_naive = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')

            start_dt_aware = start_dt_naive.replace(tzinfo=tz_ist)
            end_dt_aware = end_dt_naive.replace(tzinfo=tz_ist)

            hackathon.start_time = start_dt_aware.astimezone(ZoneInfo("UTC"))
            hackathon.end_time = end_dt_aware.astimezone(ZoneInfo("UTC"))
        except Exception:
            flash("Invalid date/time format. Please use the correct format.", "error")
            return render_template("admin/edit_hackathon.html", hackathon=hackathon, challenges=challenges)

        hackathon.name = name
        hackathon.description = description

        selected_ids = set(map(int, challenge_ids))
        selected_challenges = [c for c in challenges if c.id in selected_ids]

        # Assign updated challenges to hackathon
        hackathon.challenges = selected_challenges

        db.session.commit()
        flash("Hackathon updated!", "success")
        return redirect(url_for("admin_hackathon.edit_hackathon", id=id))

    return render_template("admin/edit_hackathon.html", hackathon=hackathon, challenges=challenges)


@admin_hackathon_bp.route('/<int:hackathon_id>')
def show_hackathon_challenges(hackathon_id):
    page = request.args.get('page', 1, type=int)
    per_page = 20

    hackathon = Hackathon.query.get_or_404(hackathon_id)
    pagination = hackathon.challenges.order_by(Challenge.id.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    challenges = pagination.items
    return render_template(
        "challenge.html",
        all_challenges=challenges,
        challenge=challenges[0] if challenges else None,
        pagination=pagination,
    )
