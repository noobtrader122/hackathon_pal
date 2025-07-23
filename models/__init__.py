"""
Data models for SQL Hackathon Platform

This package contains:
- SQLAlchemy ORM models for persistent storage (recommended in production)
- (Optionally) dataclasses for compatibility or admin utilities
- Database utilities and helper functions
"""

# --- SQLAlchemy ORM models (recommended for all routes) ---
from .sqlalchemy_models import (
    db,  # SQLAlchemy instance
    Challenge,
    TestCase,
    Submission,
    TestCaseResult,
    LeaderboardEntry,
)

# --- OPTIONALLY: Legacy dataclasses (keep ONLY for challenge import/JSON admin utils) ---
from .base import BaseModel
from .challenge import Challenge as ChallengeDataClass, TestCase as TestCaseDataClass
from .submission import Submission as SubmissionDataClass, TestCaseResult as TestCaseResultDataClass, SubmissionStatus
from .leaderboard import Leaderboard, ParticipantStats

# --- Database utilities ---
try:
    from .database_utils import DatabaseManager, ChallengeLoader, eval_sql_with_defog
except ImportError:
    DatabaseManager = None
    ChallengeLoader = None
    eval_sql_with_defog = None

__all__ = [
    # ORM models (preferred!)
    'db',
    'Challenge', 'TestCase',
    'Submission', 'TestCaseResult',
    'LeaderboardEntry',
    'BaseModel',
    'ChallengeDataClass', 'TestCaseDataClass',
    'SubmissionDataClass', 'TestCaseResultDataClass', 'SubmissionStatus',
    'Leaderboard', 'ParticipantStats',
    'DatabaseManager', 'ChallengeLoader', 'eval_sql_with_defog'
]

# Model configuration (tune as needed)
MODEL_CONFIG = {
    'max_query_results': 1000,
    'default_challenge_points': 10,
    'submission_timeout': 30
}
