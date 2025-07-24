"""
----------------------------------------------------------------------------
 Author : Rayyan Mirza
----------------------------------------------------------------------------
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from .base import BaseModel

class SubmissionStatus(Enum):
    PENDING = "pending"
    CORRECT = "correct"
    INCORRECT = "incorrect"
    ERROR = "error"
    TIMEOUT = "timeout"
    EXCEEDED_LIMIT = "exceeded_limit"

@dataclass
class TestCaseResult(BaseModel):
    """Result for a single test case"""
    test_id: int
    status: SubmissionStatus
    execution_time: float  # in seconds
    actual_result: Optional[List[List[Any]]] = None
    error_message: Optional[str] = None
    rows_returned: int = 0
    
    def __post_init__(self):
        if self.execution_time < 0:
            raise ValueError("Execution time cannot be negative")

@dataclass
class Submission(BaseModel):
    """User submission for a challenge"""
    submission_id: str  # UUID
    email: str
    challenge_id: int
    sql_query: str
    status: SubmissionStatus
    test_results: List[TestCaseResult]
    submitted_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_execution_time: float = 0.0
    score: int = 0  # Points earned
    feedback: Optional[str] = None
    
    def __post_init__(self):
        """Validation after initialization"""
        import re
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError("Invalid email format")
        
        if not self.sql_query.strip():
            raise ValueError("SQL query cannot be empty")
        
        if self.total_execution_time < 0:
            raise ValueError("Total execution time cannot be negative")
        
        if self.score < 0:
            raise ValueError("Score cannot be negative")
    
    def is_correct(self) -> bool:
        """Check if submission is completely correct"""
        return (self.status == SubmissionStatus.CORRECT and 
                all(result.status == SubmissionStatus.CORRECT 
                    for result in self.test_results))
    
    def passed_test_cases(self) -> int:
        """Count number of passed test cases"""
        return sum(1 for result in self.test_results 
                  if result.status == SubmissionStatus.CORRECT)
    
    def mark_completed(self, status: SubmissionStatus, score: int = 0):
        """Mark submission as completed"""
        self.status = status
        self.completed_at = datetime.now()
        self.score = score
