from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from models.sqlalchemy_models import Challenge, TestCase, User, db
from utils.db_utils import hash_password, verify_password
from utils.image_gen import description_to_image, generate_table_snippet_from_testcase
from datetime import datetime
import os
import json


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
        # Get and validate form fields
        errors = []
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        difficulty = request.form.get('difficulty', '').strip()
        category = request.form.get('category', '').strip()
        points_raw = request.form.get('points', '').strip()
        tc_schema = request.form.get('tc_schema', '').strip()
        tc_data = request.form.get('tc_data', '').strip()
        tc_result = request.form.get('tc_expected_result', '').strip()
        max_rows = request.form.get('max_rows', 1000)

        # Validation
        if not title:
            errors.append("Title is required.")
        if not description:
            errors.append("Description is required.")
        if not difficulty:
            errors.append("Difficulty is required.")
        try:
            points = int(points_raw) if points_raw else 10
        except ValueError:
            errors.append("Points must be an integer.")
            points = 10
        if not tc_schema:
            errors.append("Test schema is required.")
        if not tc_data:
            errors.append("Test data is required.")
        if not tc_result:
            errors.append("Expected result is required.")
        else:
            try:
                expected_result = json.loads(tc_result)
                if not isinstance(expected_result, list):
                    raise ValueError
            except Exception:
                errors.append('Expected result must be a valid JSON list of lists (e.g. [["Alice"], ["Bob"]])')
                expected_result = None

        # Early return on errors
        if errors:
            for err in errors:
                flash(err, 'danger')
            # Repopulate entered values on error
            return render_template(
                "admin/new_challenge.html",
                # The following helps prefill fields if needed
                title=title, description=description, difficulty=difficulty, category=category,
                points=points_raw, tc_schema=tc_schema, tc_data=tc_data, tc_expected_result=tc_result, max_rows=max_rows
            )

        # Create the Challenge instance
        challenge = Challenge(
            title=title,
            description=description,
            difficulty=difficulty,
            category=category,
            points=points,
            max_rows=max_rows,
        )
        db.session.add(challenge)
        db.session.flush()  # Ensure challenge.id is assigned

        # Create the sample TestCase
        now_ts = int(datetime.utcnow().timestamp())  # unique test_id (could use autoinc)
        test_case = TestCase(
            challenge_id=challenge.id,
            test_id=now_ts,
            test_schema=tc_schema,
            test_data=tc_data,
            expected_result=expected_result,
            description="Sample test case",
            max_execution_sec=30
        )
        db.session.add(test_case)
        db.session.commit()

        # Generate sample table snippet (CREATE TABLE + first 2 INSERTs)
        sample_table = generate_table_snippet_from_testcase(test_case)
        static_dir = os.path.join("static", "challenge_images")
        os.makedirs(static_dir, exist_ok=True)
        image_filename = f"challenge_{challenge.id}.png"
        abs_image_path = os.path.abspath(os.path.join(static_dir, image_filename))
        description_to_image(challenge.description, sample_table, abs_image_path)

        challenge.description_image_path = "/" + os.path.join(static_dir, image_filename).replace("\\", "/")
        db.session.commit()

        flash("Challenge added successfully!", "success")
        return redirect(url_for('admin_bp.new_challenge'))

    # GET
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

