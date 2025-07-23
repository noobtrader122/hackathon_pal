from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import os
from ..models.sqlalchemy_models import Challenge, TestCase, db
from datetime import datetime

admin_bp = Blueprint("admin_bp", __name__, url_prefix='/admin')

def admin_required(fn):
    """Decorator to protect admin views via session-based login."""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_bp.admin_login", next=request.url))
        return fn(*args, **kwargs)
    return wrapper

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == os.environ.get("ADMIN_PASSWORD", "admin"):
            session["is_admin"] = True
            flash("Admin login successful!", "success")
            next_url = request.args.get("next") or url_for("admin_bp.new_challenge")
            return redirect(next_url)
        else:
            flash("Invalid admin password", "error")
    return render_template("admin/login.html")

@admin_bp.route('/logout')
def admin_logout():
    session.pop("is_admin", None)
    flash("Logged out of admin.")
    return redirect(url_for("admin_bp.admin_login"))

@admin_bp.route('/challenges/new', methods=['GET', 'POST'])
@admin_required
def new_challenge():
    if request.method == 'POST':
        # Collect Challenge Info
        title = request.form['title'].strip()
        description = request.form['description'].strip()
        difficulty = request.form['difficulty']
        category = request.form.get('category', '').strip()
        points = int(request.form.get('points', 10))
        tc_schema = request.form['tc_schema'].strip()
        tc_data = request.form['tc_data'].strip()
        tc_result = request.form['tc_expected_result'].strip()

        # Parse expected result as JSON
        import json
        try:
            expected_result = json.loads(tc_result)
            if not isinstance(expected_result, list):
                raise ValueError
        except Exception:
            flash('Expected result must be a valid JSON list of lists (e.g. [["Alice"], ["Bob"]])', 'error')
            return render_template('admin/new_challenge.html')

        # Insert challenge and test case into the database
        challenge = Challenge(
            title=title,
            description=description,
            difficulty=difficulty,
            category=category,
            points=points,
            max_rows=1000  # Or get from config or form
        )
        db.session.add(challenge)
        db.session.flush()  # get challenge.id

        test_case = TestCase(
            challenge_id=challenge.id,
            test_id=int(datetime.utcnow().timestamp()),  # crude unique id, usually autoincremented
            test_schema=tc_schema,
            test_data=tc_data,
            expected_result=expected_result,
            description="",
            max_execution_sec=30
        )
        db.session.add(test_case)
        db.session.commit()

        flash("Challenge added successfully!", "success")
        return redirect(url_for('admin_bp.new_challenge'))

    return render_template("admin/new_challenge.html")
