"""
Routes package for SQL Hackathon Platform

This package contains all route definitions organized by functionality:
- challenge_routes: Challenge listing, viewing, and management
- submission_routes: SQL submission handling and evaluation  
- leaderboard_routes: Leaderboard display and statistics
"""

from challenge_routes import challenge_bp
from submission_routes import submission_bp  
from leaderboard_routes import leaderboard_bp

__all__ = [
    'challenge_bp',
    'submission_bp', 
    'leaderboard_bp'
]

# Route configuration
ROUTE_PREFIXES = {
    'challenges': '/challenges',
    'submissions': '/submit', 
    'leaderboard': '/leaderboard'
}
