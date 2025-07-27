"""
----------------------------------------------------------------------------
 Author : Rayyan Mirza
----------------------------------------------------------------------------
"""

from flask import Blueprint, render_template, abort, request, session
import json
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
        last_submission_output=last_submission_output
    )

