"""
----------------------------------------------------------------------------
 Author : Rayyan Mirza
----------------------------------------------------------------------------
"""

from flask import Blueprint, render_template, abort, request, session, redirect, url_for, flash
import json
from models.sqlalchemy_models import Challenge, Hackathon
from datetime import datetime, timezone
from factory import db
from typing import Optional

challenge_bp = Blueprint("challenge_bp", __name__)


@challenge_bp.route("/", defaults={"hackathon_id": None})
@challenge_bp.route("/hackathon/<int:hackathon_id>")
def list_challenges_hackathon(hackathon_id: Optional[int]):
    """
    List challenges paginated.
    Optionally filter by hackathon_id using many-to-many relation.
    Shows first challenge as default detail.

    URL examples:
    - /                      -> all challenges (paginated)
    - /hackathon/123         -> challenges for hackathon 123 (paginated)
    """
    page = request.args.get("page", 1, type=int)
    per_page = 20

    if hackathon_id is not None:
        hackathon = Hackathon.query.get(hackathon_id)
        if not hackathon:
            abort(404, description="Hackathon not found.")

        pagination = hackathon.challenges.order_by(Challenge.id.asc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        challenges = pagination.items
    else:
        pagination = Challenge.query.order_by(Challenge.id.asc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        challenges = pagination.items

    # Show first challenge as detail or None if no challenges
    first_challenge = challenges[0] if challenges else None
    is_first_challenge = first_challenge is not None

    return render_template(
        "challenge.html",
        all_challenges=challenges,
        challenge=first_challenge,
        pagination=pagination,
        hackathon_id=hackathon_id,
        first_challenge=first_challenge,
        is_first_challenge=is_first_challenge,
    )


@challenge_bp.route("/hackathon/<int:hackathon_id>/challenge/<int:cid>")
def challenge_page(hackathon_id: int, cid: int):
    challenge = Challenge.query.get_or_404(cid)
    hackathon = Hackathon.query.get_or_404(hackathon_id)

    last_output_json = session.pop("last_submission_output", None)
    last_submission_output = json.loads(last_output_json) if last_output_json else None
    sql_query = session.get("sql_query")

    if challenge not in hackathon.challenges:
        abort(404, description="Challenge not part of this hackathon.")

    challenges = hackathon.challenges.order_by(Challenge.id.asc()).all()

    solved_ids = set(session.get("solved_ids", []))
    for c in challenges:
        c.solved = c.id in solved_ids

    challenge_ids = [c.id for c in challenges]
    idx = challenge_ids.index(cid)

    prev_challenge = challenges[idx - 1] if idx > 0 else None
    next_challenge = challenges[idx + 1] if idx < len(challenges) - 1 else None

    now_utc = datetime.now(timezone.utc)

    hackathon_start_iso = hackathon.start_time.isoformat() if hackathon.start_time else None
    hackathon_end_iso = hackathon.end_time.isoformat() if hackathon.end_time else None

    return render_template(
        "challenge.html",
        challenge=challenge,
        all_challenges=challenges,
        prev_challenge=prev_challenge,
        next_challenge=next_challenge,
        hackathon_start_iso=hackathon_start_iso,
        hackathon_end_iso=hackathon_end_iso,
        now_iso=now_utc.isoformat(),
        hackathon_id=hackathon_id,
        last_submission_output=last_submission_output,
        sql_query=sql_query
    )

@challenge_bp.route('/edit/<int:cid>', methods=['GET', 'POST'])
def edit_challenge(cid):
    if not session.get('is_admin'):
        flash('You must be logged in to edit a challenge.', 'error')
        return redirect(url_for('admin_bp.login'))
    
    challenge = Challenge.query.get_or_404(cid)
    if request.method == 'POST':
        try:
            # Get and validate form data
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            difficulty = request.form.get('difficulty', '').strip().lower()
            category = request.form.get('category', '').strip()
            points = request.form.get('points', type=int)
            max_rows = request.form.get('max_rows', type=int)

            # Validate required fields
            errors = []
            if not title:
                errors.append("Title is required.")
            if not description:
                errors.append("Description is required.")
            if not difficulty:
                errors.append("Difficulty is required.")
            if not points:
                errors.append("Points value is required.")
            if max_rows is None:
                # Optionally allow max_rows to be optional, otherwise:
                errors.append("Max Rows is required.")

            if errors:
                for err in errors:
                    flash(err, 'error')
                # Repopulate form with entered data on error
                return render_template('admin/edit_challenge.html', challenge=challenge)

            # Update challenge object
            challenge.title = title
            challenge.description = description
            challenge.difficulty = difficulty
            challenge.category = category
            challenge.points = points
            challenge.max_rows = max_rows

            db.session.commit()
            flash('Challenge updated successfully!', 'success')
            # Redirect to challenge list, or stay on edit page (adjust as needed)
            return redirect(url_for('challenge_bp.edit_challenge', cid=cid))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating challenge: {e}', 'error')
            return render_template('admin/edit_challenge.html', challenge=challenge)

    # GET: Render the form pre-filled with challenge data
    return render_template('admin/edit_challenge.html', challenge=challenge)

@challenge_bp.route("/list_challenges")
def list_challenges():
    challenges = Challenge.query.order_by(Challenge.id).all()
    return render_template("/admin/challenge_list.html", challenges=challenges)

