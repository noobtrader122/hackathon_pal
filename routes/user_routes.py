from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.sqlalchemy_models import User, db
from utils.db_utils import hash_password, verify_password

user_bp = Blueprint("user_bp", __name__, url_prefix="/user")

@user_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # --- Basic input validation ---
        error = None
        if not email or not username or not password or not confirm_password:
            error = "All fields are required."
        elif "@" not in email:
            error = "Invalid email address."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif User.query.filter( (User.email == email) | (User.username == username) ).first():
            error = "A user with this email or username already exists."

        if error:
            flash(error, "danger")
            return render_template("user/register.html")

        # --- Account creation ---
        user = User(
            email=email,
            username=username,
            password=hash_password(password),
            is_admin=False,
            is_active=True,
            is_authenticated=True
        )
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("user_bp.login"))

    return render_template("user/register.html")

@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and verify_password(password, user.password):
            if user.is_active:
                session.clear()
                session["user_id"] = user.id
                session["username"] = user.username
                session["is_authenticated"] = True
                flash("Logged in successfully.", "success")
                return redirect(url_for("user_bp.user_dashboard"))
            else:
                flash("Account not active. Contact support.", "warning")
        else:
            flash("Invalid credentials.", "danger")
    return render_template("user/login.html")

@user_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("user_bp.login"))


@user_bp.route("/profile")
def user_profile():
    user = User.query.get(session.get("user_id"))
    return render_template("user/profile.html", user=user)


@user_bp.route("/dashboard")
def user_dashboard():
    # Only logged-in users can access
    if not session.get("is_authenticated"):
        return redirect(url_for("user_bp.login"))
    # user-specific info
    return render_template("user/dashboard.html")
