from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from models.sqlalchemy_models import Challenge, TestCase, User, db
from utils.db_utils import hash_password, verify_password
from datetime import datetime

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")

def admin_required(fn):
    """Decorator to protect admin views via session-based login."""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin login required.", "warning")
            # Pass 'next' param to support post-login redirects
            return redirect(url_for("admin_bp.admin_login", next=request.url))
        return fn(*args, **kwargs)
    return wrapper

######################################################################
# Admin Login/Logout
######################################################################
@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and verify_password(password, user.password):
            if user.is_admin:
                session.clear()
                # Optional: session.permanent = True (for longer admin logins)
                session["user_id"] = user.id
                session["is_admin"] = True
                session["username"] = user.username
                flash("Logged in as admin.", "success")
                next_url = request.args.get("next") or url_for("admin_bp.admin_dashboard")
                return redirect(next_url)
            elif not user.is_active or not user.is_authenticated:
                flash("Account is either not active or not authenticated.", "danger")
                return render_template("index.html")
            else:
                flash("You are not an admin account.", "warning")
                return redirect(url_for("user_bp.user_dashboard"))
        else:
            flash("Invalid username or password.", "danger")
    return render_template("admin/login.html")

@admin_bp.route("/logout")
def admin_logout():
    session.clear()
    flash("Logged out of admin.", "info")
    return redirect(url_for("admin_bp.admin_login"))

######################################################################
# Admin Dashboard (Example, you should implement the template)
######################################################################
@admin_bp.route("/")
@admin_required
def admin_dashboard():
    # Example: list all challenges/users, or admin stats
    user_count = User.query.count()
    challenge_count = Challenge.query.count()
    return render_template("admin/dashboard.html", user_count=user_count, challenge_count=challenge_count)

######################################################################
# Challenge Creation
######################################################################
@admin_bp.route("/challenges/new", methods=["GET", "POST"])
@admin_required
def new_challenge():
    if request.method == "POST":
        title = request.form['title'].strip()
        description = request.form['description'].strip()
        difficulty = request.form['difficulty']
        category = request.form.get('category', '').strip()
        try:
            points = int(request.form.get('points', 10))
        except Exception:
            flash('Points must be an integer.', 'danger')
            return render_template("admin/new_challenge.html")
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
            flash('Expected result must be a valid JSON list of lists (e.g. [["Alice"], ["Bob"]])', 'danger')
            return render_template('admin/new_challenge.html')

        # Insert Challenge and TestCase
        challenge = Challenge(
            title=title,
            description=description,
            difficulty=difficulty,
            category=category,
            points=points,
            max_rows=1000
        )
        db.session.add(challenge)
        db.session.flush()  # get challenge.id

        test_case = TestCase(
            challenge_id=challenge.id,
            test_id=int(datetime.utcnow().timestamp()),  # unique id (better: use db autoinc if possible)
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

######################################################################
# Register User (Admin adds new user – use strong password rules)
######################################################################
@admin_bp.route("/add_user", methods=["GET", "POST"])
@admin_required
def add_user():
    if request.method == 'POST':
        email = request.form['email'].strip()
        username = request.form['username'].strip()
        password = request.form['password']

        if len(password) < 8 or not any(c.isdigit() for c in password):
            flash("Password must be at least 8 characters, containing numbers.", "warning")
            return render_template("admin/add_user.html")

        # Check for existing user
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already exists.", "danger")
            return render_template("admin/add_user.html")

        user = User(email=email, username=username, password=hash_password(password))
        db.session.add(user)
        db.session.commit()
        flash("User added successfully!", "success")
        return redirect(url_for("admin_bp.admin_dashboard"))  # Or redirect as needed

    return render_template("admin/add_user.html")

