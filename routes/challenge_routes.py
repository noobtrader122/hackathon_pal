"""
----------------------------------------------------------------------------
 Author : Rayyan Mirza
----------------------------------------------------------------------------
"""

from flask import Blueprint, render_template, abort, request, session
from models.sqlalchemy_models import Challenge, Hackathon
from datetime import datetime, timezone
from typing import Optional

challenge_bp = Blueprint("challenge_bp", __name__)


@challenge_bp.route("/", defaults={"hackathon_id": None})
@challenge_bp.route("/hackathon/<int:hackathon_id>")
def list_challenges(hackathon_id: Optional[int]):
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

    return render_template(
        "challenge.html",
        all_challenges=challenges,
        challenge=first_challenge,
        pagination=pagination,
    )


@challenge_bp.route("/challenge/<int:cid>")
def challenge_page(cid: int):
    """
    Displays the challenge detail page for challenge id `cid`,
    including navigation, solved marking, and the global hackathon timer.
    """
    # Fetch requested challenge or 404
    challenge = Challenge.query.get_or_404(cid)

    # Get hackathons for the challenge (many-to-many)
    if challenge.hackathons.count() == 0:
        abort(404, description="Hackathon not found for this challenge.")
    # Assume first hackathon for timer purposes
    hackathon = challenge.hackathons.first()

    # Fetch all challenges for the hackathon (sidebar/navigation)
    challenges = hackathon.challenges.order_by(Challenge.id.asc()).all()

    # Mark solved challenges based on session info
    solved_ids = set(session.get("solved_ids", []))
    for c in challenges:
        c.solved = c.id in solved_ids

    # Navigation: previous and next challenges within hackathon
    challenge_ids = [c.id for c in challenges]
    try:
        idx = challenge_ids.index(cid)
    except ValueError:
        abort(404, description="Challenge not found in hackathon challenges.")

    prev_challenge = challenges[idx - 1] if idx > 0 else None
    next_challenge = challenges[idx + 1] if idx < len(challenges) - 1 else None

    # Timer: use per-challenge time limit or default 10 min (600 seconds)
    time_limit_sec = getattr(challenge, "time_limit_sec", 600)

    now_utc = datetime.now(timezone.utc)

    hackathon_start_iso = (
        hackathon.start_time.isoformat() if hackathon.start_time else None
    )
    hackathon_end_iso = hackathon.end_time.isoformat() if hackathon.end_time else None

    # If you have app logger:
    # from flask import current_app
    # current_app.logger.debug(f"Hackathon times: start={hackathon_start_iso}, end={hackathon_end_iso}")

    return render_template(
        "challenge.html",
        challenge=challenge,
        all_challenges=challenges,
        prev_challenge=prev_challenge,
        next_challenge=next_challenge,
        time_limit_sec=time_limit_sec,
        hackathon_start_iso=hackathon_start_iso,
        hackathon_end_iso=hackathon_end_iso,
        now_iso=now_utc.isoformat(),
    )
