"""
SQLAlchemy ORM models for the SQL-Hackathon platform.
Run `flask db migrate && flask db upgrade` after adding or changing fields.
"""

import uuid
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

db = SQLAlchemy()  # imported and initialized in __init__.py


# ------------------------------------------------------------------------
# Association table for many-to-many Hackathon ↔ Challenge link
# ------------------------------------------------------------------------
hackathon_challenge_association = db.Table(
    'hackathon_challenges',
    db.Column('hackathon_id', db.Integer, db.ForeignKey('hackathon.id'), primary_key=True),
    db.Column('challenge_id', db.Integer, db.ForeignKey('challenge.id'), primary_key=True)
)


# ------------------------------------------------------------------------
# Hackathon
# ------------------------------------------------------------------------
class Hackathon(db.Model):
    __tablename__ = "hackathon"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime(timezone=True), nullable=False)
    end_time = db.Column(db.DateTime(timezone=True), nullable=False)

    # Many-to-many relationship to Challenge via association table
    challenges = relationship(
        'Challenge',
        secondary=hackathon_challenge_association,
        back_populates='hackathons',
        lazy='dynamic'
    )

    def __repr__(self):
        return f"<Hackathon {self.name}>"


# ---------------------------------------------------------------------------
# MIX-INS & BASE
# ---------------------------------------------------------------------------
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


# ---------------------------------------------------------------------------
# CHALLENGE & TEST-CASE
# ---------------------------------------------------------------------------
class Challenge(db.Model, TimestampMixin):
    """Top-level contest problem."""
    __tablename__ = "challenge"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(
        db.Enum("easy", "medium", "hard", name="difficulty_enum"),
        nullable=False,
        index=True
    )
    category = db.Column(db.String(80), nullable=True)
    points = db.Column(db.Integer, nullable=False, default=10)
    max_rows = db.Column(db.Integer, nullable=False, default=1000)

    # Remove single hackathon_id FK since replaced by many-to-many relationship
    # hackathon_id = db.Column(db.Integer, db.ForeignKey('hackathon.id'))

    # Many-to-many backref to Hackathon
    hackathons = relationship(
        'Hackathon',
        secondary=hackathon_challenge_association,
        back_populates='challenges',
        lazy='dynamic'
    )

    # Relationships
    test_cases = relationship(
        "TestCase",
        back_populates="challenge",
        cascade="all, delete-orphan",
        order_by="TestCase.test_id"
    )

    submissions = relationship(
        "Submission",
        back_populates="challenge",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Challenge {self.id} – {self.title}>"


class TestCase(db.Model):
    """One data scenario for a challenge."""
    __tablename__ = "test_case"
    __table_args__ = (
        db.UniqueConstraint("challenge_id", "test_id", name="uix_challenge_testid"),
    )

    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(
        db.Integer,
        db.ForeignKey("challenge.id", ondelete="CASCADE"),
        nullable=False
    )

    test_id = db.Column(db.Integer, nullable=False)
    test_schema = db.Column(db.Text, nullable=False)
    test_data = db.Column(db.Text, nullable=False)
    expected_result = db.Column(JSON, nullable=False)
    description = db.Column(db.String(255))
    max_execution_sec = db.Column(db.Integer, nullable=False, default=30)

    # Relationships
    challenge = relationship("Challenge", back_populates="test_cases")

    def __repr__(self):
        return f"<TestCase {self.test_id} of Challenge {self.challenge_id}>"


# ---------------------------------------------------------------------------
# SUBMISSION & TEST-CASE-RESULT
# ---------------------------------------------------------------------------
class Submission(db.Model, TimestampMixin):
    """A user’s answer to a challenge at a point in time."""
    __tablename__ = "submission"
    __table_args__ = (db.Index("ix_submission_email", "email"),)

    id = db.Column(db.Integer, primary_key=True)
    submission_uid = db.Column(
        db.String(36),
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False
    )
    email = db.Column(db.String(120), nullable=False)
    challenge_id = db.Column(
        db.Integer,
        db.ForeignKey("challenge.id", ondelete="CASCADE"),
        nullable=False
    )

    sql_query = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.Enum(
            "pending",
            "correct",
            "incorrect",
            "timeout",
            "error",
            "exceeded_limit",
            name="submission_status_enum"
        ),
        nullable=False,
        default="pending"
    )
    total_time_sec = db.Column(db.Float, nullable=False, default=0.0)
    score = db.Column(db.Integer, nullable=False, default=0)

    # Relationships
    challenge = relationship("Challenge", back_populates="submissions")
    tc_results = relationship(
        "TestCaseResult",
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="TestCaseResult.test_id"
    )

    def __repr__(self):
        return f"<Submission {self.submission_uid} – {self.email}>"


class TestCaseResult(db.Model):
    """Outcome of a submission on one test case."""
    __tablename__ = "test_case_result"
    __table_args__ = (
        db.UniqueConstraint("submission_id", "test_id", name="uix_sub_test"),
    )

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer,
        db.ForeignKey("submission.id", ondelete="CASCADE"),
        nullable=False
    )

    test_id = db.Column(db.Integer, nullable=False)
    status = db.Column(
        db.Enum(
            "correct",
            "incorrect",
            "timeout",
            "error",
            name="tc_status_enum"
        ),
        nullable=False
    )
    execution_time = db.Column(db.Float, nullable=False)
    rows_returned = db.Column(db.Integer, nullable=False, default=0)
    actual_result = db.Column(JSON)  # null if error/timeout
    error_message = db.Column(db.Text)

    # Relationships
    submission = relationship("Submission", back_populates="tc_results")

    def __repr__(self):
        return f"<TCResult sub={self.submission_id} test={self.test_id} {self.status}>"


# ---------------------------------------------------------------------------
# LEADERBOARD
# ---------------------------------------------------------------------------
class LeaderboardEntry(db.Model, TimestampMixin):
    """
    Denormalised scoreboard; one row per participant.
    Updated after each correct submission.
    """
    __tablename__ = "leaderboard_entry"

    email = db.Column(db.String(120), primary_key=True)
    total_score = db.Column(db.Integer, default=0, nullable=False)
    challenges_solved = db.Column(db.Integer, default=0, nullable=False)
    challenges_attempted = db.Column(db.Integer, default=0, nullable=False)
    best_submission_time = db.Column(db.Float)  # nullable until first correct
    last_submission = db.Column(db.DateTime)

    def success_rate(self) -> float:
        if self.challenges_attempted == 0:
            return 0.0
        return self.challenges_solved / self.challenges_attempted * 100

    def __repr__(self):
        return f"<LB {self.email} score={self.total_score} solved={self.challenges_solved}>"


# -------------------------------------------------------------------
# User
# -------------------------------------------------------------------
class User(db.Model, TimestampMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_authenticated = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"
