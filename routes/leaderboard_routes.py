"""
--------------------------------------------------------------------------------------------------
    Author:   Rayyan Mirza
    Purpose:  Leaderboard routes
--------------------------------------------------------------------------------------------------
"""

from flask import Blueprint, render_template, current_app
from models import Submission, LeaderboardEntry

leaderboard_bp = Blueprint("leaderboard_bp", __name__)

@leaderboard_bp.route("/")
def show_leaderboard():
    """
    Show leaderboard, source from LeaderboardEntry model if present,
    or SQL aggregate on Submission as fallback.
    """
    source = current_app.config.get("LEADERBOARD_DATA_SOURCE", "database")

    if source == "aggregate":
        # Fallback: aggregate submissions on the fly (less efficient for big tables)
        result = Submission.query.with_entities(
            Submission.email,
            db.func.sum(Submission.score).label('total_score')
        ).group_by(Submission.email).order_by(db.desc('total_score')).all()
        rows = [
            {"email": row.email, "total_score": row.total_score}
            for row in result
        ]
    else:
        # Recommended: use LeaderboardEntry model, fast and always current
        rows = LeaderboardEntry.query.order_by(LeaderboardEntry.total_score.desc()).all()

    return render_template("leaderboard.html", rows=rows)
