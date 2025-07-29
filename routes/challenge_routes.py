"""
----------------------------------------------------------------------------
 Author : Rayyan Mirza
 Modified by AI assistant for clarity, DRY, and image generation
----------------------------------------------------------------------------
"""

from flask import Blueprint, render_template, abort, request, session, redirect, url_for, flash
from models.sqlalchemy_models import Challenge, Hackathon, TestCase
from datetime import datetime, timezone
from factory import db
from typing import Optional
import os
import json

# Image generation utilities
from utils.image_gen import description_to_image, generate_table_snippet_from_testcase

challenge_bp = Blueprint("challenge_bp", __name__)

def validate_challenge_form(form):
    errors = []
    # Required fields validation
    title = form.get('title', '').strip()
    description = form.get('description', '').strip()
    difficulty = form.get('difficulty', '').strip().lower()
    category = form.get('category', '').strip()
    points = form.get('points', type=int)
    max_rows = form.get('max_rows', type=int)

    # Test case related fields
    tc_schema = form.get('tc_schema', '').strip()
    tc_data = form.get('tc_data', '').strip()
    tc_result = form.get('tc_expected_result', '').strip()

    # Parse expected result
    expected_result = None
    if tc_result:
        try:
            expected_result = json.loads(tc_result)
            if not isinstance(expected_result, list):
                raise ValueError
        except Exception:
            errors.append('Expected result must be a valid JSON list of lists (e.g. [["Alice"], ["Bob"]])')

    # Field presence checks
    if not title:
        errors.append("Title is required.")
    if not description:
        errors.append("Description is required.")
    if not difficulty:
        errors.append("Difficulty is required.")
    if not points:
        errors.append("Points value is required.")
    if max_rows is None:
        errors.append("Max Rows is required.")
    if not tc_schema:
        errors.append("Test schema is required.")
    if not tc_data:
        errors.append("Test data is required.")
    if not tc_result:
        errors.append("Expected result is required.")

    return errors, {
        "title": title,
        "description": description,
        "difficulty": difficulty,
        "category": category,
        "points": points,
        "max_rows": max_rows,
        "tc_schema": tc_schema,
        "tc_data": tc_data,
        "expected_result": expected_result,
    }

@challenge_bp.route("/", defaults={"hackathon_id": None})
@challenge_bp.route("/hackathon/<int:hackathon_id>")
def list_challenges_hackathon(hackathon_id: Optional[int]):
    """
    List challenges paginated.
    Optionally filter by hackathon_id using many-to-many relation.
    Shows first challenge as default detail.
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
    test_case = TestCase.query.filter_by(challenge_id=cid).order_by(TestCase.test_id.asc()).first()

    if request.method == 'POST':
        errors, form = validate_challenge_form(request.form)

        if errors:
            for err in errors:
                flash(err, 'error')
            # Repopulate form with entered data on error
            return render_template('admin/edit_challenge.html', challenge=challenge, test_case=test_case)

        # Update challenge
        challenge.title = form["title"]
        challenge.description = form["description"]
        challenge.difficulty = form["difficulty"]
        challenge.category = form["category"]
        challenge.points = form["points"]
        challenge.max_rows = form["max_rows"]

        # Update test case if present
        if test_case:
            test_case.test_schema = form["tc_schema"]
            test_case.test_data = form["tc_data"]
            test_case.expected_result = form["expected_result"]

        db.session.commit()

        # Generate image with description and table sample
        static_dir = os.path.join("static", "challenge_images")
        os.makedirs(static_dir, exist_ok=True)
        image_filename = f"challenge_{challenge.id}.png"
        abs_image_path = os.path.abspath(os.path.join(static_dir, image_filename))

        sample_table = generate_table_snippet_from_testcase(test_case) if test_case else ""
        description_to_image(challenge.description, sample_table, abs_image_path)

        challenge.description_image_path = "/" + os.path.join(static_dir, image_filename).replace("\\", "/")
        db.session.commit()

        flash('Challenge updated successfully!', 'success')
        return redirect(url_for('challenge_bp.edit_challenge', cid=cid))

    # GET: Render the form pre-filled with challenge data and test_case
    return render_template('admin/edit_challenge.html', challenge=challenge, test_case=test_case)

@challenge_bp.route("/list_challenges")
def list_challenges():
    challenges = Challenge.query.order_by(Challenge.id).all()
    return render_template("/admin/challenge_list.html", challenges=challenges)
