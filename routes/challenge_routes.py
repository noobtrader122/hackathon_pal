"""
----------------------------------------------------------------------------
 Author : Rayyan Mirza
----------------------------------------------------------------------------
"""

from flask import Blueprint, render_template, abort, current_app, request,session
from ..models import Challenge
from ..models.database_utils import ChallengeLoader

challenge_bp = Blueprint("challenge_bp", __name__)

@challenge_bp.route("/")
def list_challenges():
    """
    List all challenges (from DB or JSON, depending on config)
    """
    source = current_app.config.get("CHALLENGES_DATA_SOURCE", "database")
    if source == "json":
        # JSON loader path (legacy/dev)
        challenges = ChallengeLoader.load_from_json(
            current_app.config["CHALLENGES_JSON_FILE"]
        )
    else:
        # SQLAlchemy ORM path (production-ready)
        # Optionally, paginate or order here
        page = request.args.get('page', 1, type=int)
        per_page = 20
        pagination = Challenge.query.order_by(Challenge.id.asc()).paginate(page=page, per_page=per_page, error_out=False)
        challenges = pagination.items
    return render_template(
        "index.html",
        challenges=challenges,
        pagination=pagination if source != "json" else None
    )

@challenge_bp.route("/<int:cid>")
def challenge_page(cid):
    # Get all challenges in consistent order
    challenges = Challenge.query.order_by(Challenge.id).all()
    challenge = Challenge.query.get_or_404(cid)

    # (Optional) - Marking solved/attempted challenges if user data available:
    # Suppose you have user progress in the session or DB.
    # For this example, let's say session['solved_ids'] = [1,2,...]
    solved_ids = set(session.get("solved_ids", []))
    for c in challenges:
        c.solved = c.id in solved_ids

    # Find index for navigation
    challenge_ids = [c.id for c in challenges]
    idx = challenge_ids.index(cid)
    prev_challenge = challenges[idx - 1] if idx > 0 else None
    next_challenge = challenges[idx + 1] if idx < len(challenges) - 1 else None

    # Timer: you can set per-challenge or a global default
    # e.g. challenge.time_limit_sec or a config value
    time_limit_sec = getattr(challenge, "time_limit_sec", 600)    # fallback to 10m default

    return render_template(
        "challenge.html",
        challenge=challenge,
        all_challenges=challenges,
        prev_challenge=prev_challenge,
        next_challenge=next_challenge,
        time_limit_sec=time_limit_sec
    )
