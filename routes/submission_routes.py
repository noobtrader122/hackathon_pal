"""
------------------------------------------------------
 Author : Rayyan Mirza
------------------------------------------------------
"""

from flask import Blueprint, request, redirect, url_for, flash, session as flask_session
from sqlalchemy.exc import DataError, StatementError
from models.sqlalchemy_models import (
    Challenge, Submission, TestCaseResult, LeaderboardEntry, User
)
from models.database_utils import eval_sql_with_defog
from factory import db
from datetime import datetime
import uuid
import time
import json

submission_bp = Blueprint("submission_bp", __name__)


def normalize_status(status_str: str) -> str:
    """
    Normalize incoming status string to match Postgres enum values.

    Adjust the valid enums below to match exactly with your Postgres enum type.
    """
    valid_enum_values = {"passed", "failed", "error", "timeout", "skipped", "correct"}

    if not status_str:
        return "error"

    status_lower = status_str.lower()
    if status_lower in valid_enum_values:
        return status_lower
    else:
        # If unknown status, default to 'error'
        return "error"


@submission_bp.route("/<int:cid>", methods=["POST"])
def handle_submission(cid):
    user_id = flask_session.get("user_id")
    if not user_id:
        flash("You must be logged in to submit.", "error")
        return redirect(url_for("auth_bp.login"))

    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("auth_bp.login"))

    email = user.email
    hackathon_id = request.form.get("hackathon_id", type=int)
    challenge = Challenge.query.get_or_404(cid)
    sql_query = request.form.get("sql", "").strip()

    if not sql_query:
        flash("SQL query is required.", "error")
        if not hackathon_id:
            return redirect(url_for("admin_hackathon.list_hackathons"))
        return redirect(url_for("challenge_bp.challenge_page", hackathon_id=hackathon_id, cid=cid))

    flask_session['sql_query'] = sql_query
    try:
        # Evaluate submission
        start = time.perf_counter()
        passed, feedback, test_results = eval_sql_with_defog(challenge, sql_query)
        exec_time = time.perf_counter() - start

        # Save submission record
        submission = Submission(
            submission_uid=str(uuid.uuid4()),
            email=email,
            challenge_id=cid,
            sql_query=sql_query,
            status="correct" if passed else "incorrect",
            total_time_sec=exec_time,
            score=challenge.points if passed else 0
        )
        db.session.add(submission)
        db.session.flush()  # To assign submission.id before adding TestCaseResults

        # Save each test case result with normalized status to avoid enum issues
        for result in test_results:
            result_dict = result.to_dict() if hasattr(result, 'to_dict') else dict(result)
            status_val = result_dict.get("status")
            raw_status = status_val.name if hasattr(status_val, "name") else str(status_val)
            normalized_status = normalize_status(raw_status)

            tcr = TestCaseResult(
                submission_id=submission.id,
                test_id=result_dict.get("test_id"),
                status=normalized_status,
                execution_time=result_dict.get("execution_time"),
                rows_returned=result_dict.get("rows_returned"),
                actual_result=result_dict.get("actual_result"),
                error_message=result_dict.get("error_message"),
            )
            db.session.add(tcr)

        # Update leaderboard
        lb = LeaderboardEntry.query.filter_by(email=email).first()
        if lb is None:
            lb = LeaderboardEntry(
                email=email,
                challenges_attempted=0,
                challenges_solved=0,
                total_score=0,
                best_submission_time=None,
                last_submission=None
            )
            db.session.add(lb)

        # Defensive initialization to zero if None
        lb.challenges_attempted = lb.challenges_attempted or 0
        lb.challenges_solved = lb.challenges_solved or 0
        lb.total_score = lb.total_score or 0

        lb.challenges_attempted += 1

        if passed:
            lb.challenges_solved += 1
            lb.total_score += challenge.points
            if lb.best_submission_time is None or exec_time < lb.best_submission_time:
                lb.best_submission_time = exec_time

        lb.last_submission = datetime.utcnow()

        db.session.commit()

        # Store last submission output in session to show on challenge page
        last_output = []
        for result in test_results:
            r = result.to_dict() if hasattr(result, "to_dict") else dict(result)
            last_output.append({
                "test_id": r.get("test_id"),
                "status": normalize_status(r.get("status").name if hasattr(r.get("status"), "name") else str(r.get("status"))),
                "error_message": r.get("error_message"),
                "actual_result": r.get("actual_result"),
            })
        flask_session["last_submission_output"] = json.dumps(last_output)

    except (DataError, StatementError) as db_exc:
        db.session.rollback()
        flash(
            "Submission error: Invalid data or SQL error detected. Please check your SQL query and try again.",
            "error"
        )
        # Optional: add logging here for db_exc
        return redirect(url_for("challenge_bp.challenge_page", hackathon_id=hackathon_id, cid=cid))

    except Exception as exc:
        db.session.rollback()
        flash("An unexpected error occurred while processing your submission. Please try again.", "error")
        # Optional: add logging here for exc
        return redirect(url_for("challenge_bp.challenge_page", hackathon_id=hackathon_id, cid=cid))

    flash(feedback, "success" if passed else "error")
    if not hackathon_id:
        if passed:
            flash("Challenge solved!", "success")
        return redirect(url_for("admin_hackathon.list_hackathons"))
    return redirect(url_for("challenge_bp.challenge_page", hackathon_id=hackathon_id, cid=cid))
