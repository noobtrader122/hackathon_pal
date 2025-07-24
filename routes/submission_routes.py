"""
------------------------------------------------------
 Author : Rayyan Mirza
------------------------------------------------------
"""

from flask import Blueprint, request, redirect, url_for, flash
from models.sqlalchemy_models import (
    Challenge, Submission, TestCaseResult, LeaderboardEntry
)
from models.database_utils import eval_sql_with_defog
from factory import db
from datetime import datetime
import uuid
import time

submission_bp = Blueprint("submission_bp", __name__)

@submission_bp.route("/<int:cid>", methods=["POST"])
def handle_submission(cid):
    challenge = Challenge.query.get_or_404(cid)
    email = request.form.get("email", "").strip().lower()
    sql_query = request.form.get("sql", "").strip()
    print(f'sql_query {sql_query}')
    if not email or not sql_query:
        flash("Email and SQL are required.", "error")
        return redirect(url_for("challenge_bp.challenge_page", cid=cid))

    # Evaluate submission
    start = time.perf_counter()
    passed, feedback, test_results = eval_sql_with_defog(challenge, sql_query)
    exec_time = time.perf_counter() - start

    # Save Submission
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
    db.session.flush()  # So submission.id is available for TestCaseResult

    # Save TestCaseResults
    for result in test_results:
        result_dict = result.to_dict() if hasattr(result, 'to_dict') else dict(result)
        status_val = result_dict.get("status")
        status_str = status_val.name if hasattr(status_val, "name") else str(status_val)
        tcr = TestCaseResult(
            submission_id=submission.id,
            test_id=result_dict.get("test_id"),
            status=status_str,
            execution_time=result_dict.get("execution_time"),
            rows_returned=result_dict.get("rows_returned"),
            actual_result=result_dict.get("actual_result"),
            error_message=result_dict.get("error_message"),
        )
        db.session.add(tcr)

    # Update leaderboard
    lb = LeaderboardEntry.query.get(email)
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
    # Defensive: always ensure integers, even if SQL default is not set right
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

    flash(feedback, "success" if passed else "error")
    return redirect(url_for("challenge_bp.challenge_page", cid=cid))


