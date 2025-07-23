"""
--------------------------------------------------------------------------------
    Author: Rayyan Mirza
--------------------------------------------------------------------------------
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .base import BaseModel

@dataclass
class ParticipantStats(BaseModel):
    """Statistics for a single participant"""
    email: str
    total_score: int = 0
    challenges_solved: int = 0
    challenges_attempted: int = 0
    total_submissions: int = 0
    best_submission_time: Optional[float] = None
    last_submission: Optional[datetime] = None
    first_submission: Optional[datetime] = None
    average_score_per_challenge: float = 0.0
    
    def __post_init__(self):
        """Validation and calculations"""
        import re
        
        # Validate email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError("Invalid email format")
        
        if self.total_score < 0:
            raise ValueError("Total score cannot be negative")
        
        if self.challenges_solved < 0:
            raise ValueError("Challenges solved cannot be negative")
        
        if self.challenges_attempted < 0:
            raise ValueError("Challenges attempted cannot be negative")
        
        if self.challenges_solved > self.challenges_attempted:
            raise ValueError("Challenges solved cannot exceed challenges attempted")
        
        # Calculate average score
        if self.challenges_attempted > 0:
            self.average_score_per_challenge = self.total_score / self.challenges_attempted
    
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.challenges_attempted == 0:
            return 0.0
        return (self.challenges_solved / self.challenges_attempted) * 100
    
    def update_stats(self, submission_score: int, is_correct: bool, submission_time: float):
        """Update stats with new submission"""
        self.total_submissions += 1
        self.total_score += submission_score
        
        if is_correct:
            self.challenges_solved += 1
        
        # Update timing
        if self.best_submission_time is None or submission_time < self.best_submission_time:
            self.best_submission_time = submission_time
        
        now = datetime.now()
        self.last_submission = now
        
        if self.first_submission is None:
            self.first_submission = now
        
        # Recalculate averages
        if self.challenges_attempted > 0:
            self.average_score_per_challenge = self.total_score / self.challenges_attempted

@dataclass
class Leaderboard(BaseModel):
    """Overall leaderboard management"""
    participants: Dict[str, ParticipantStats] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def add_or_update_participant(self, email: str, 
                                submission_score: int = 0, 
                                is_correct: bool = False,
                                submission_time: float = 0.0):
        """Add new participant or update existing one"""
        if email not in self.participants:
            self.participants[email] = ParticipantStats(email=email)
        
        self.participants[email].update_stats(submission_score, is_correct, submission_time)
        self.last_updated = datetime.now()
    
    def get_rankings(self, limit: Optional[int] = None) -> List[Tuple[int, ParticipantStats]]:
        """Get ranked list of participants"""
        # Sort by total score (descending), then by challenges solved (descending),
        # then by best submission time (ascending)
        sorted_participants = sorted(
            self.participants.values(),
            key=lambda p: (
                -p.total_score,  # Higher score is better
                -p.challenges_solved,  # More solved is better
                p.best_submission_time if p.best_submission_time else float('inf')  # Lower time is better
            )
        )
        
        rankings = [(i + 1, participant) for i, participant in enumerate(sorted_participants)]
        
        if limit:
            return rankings[:limit]
        return rankings
    
    def get_participant_rank(self, email: str) -> Optional[int]:
        """Get rank for specific participant"""
        rankings = self.get_rankings()
        for rank, participant in rankings:
            if participant.email == email:
                return rank
        return None
    
    def get_top_performers(self, n: int = 10) -> List[ParticipantStats]:
        """Get top N performers"""
        rankings = self.get_rankings(limit=n)
        return [participant for _, participant in rankings]
