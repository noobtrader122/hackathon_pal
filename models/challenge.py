"""
----------------------------------------------------------------------------
 Author : Rayyan Mirza
----------------------------------------------------------------------------
"""


from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from base import BaseModel

@dataclass
class TestCase(BaseModel):
    """Individual test case for a challenge"""
    test_id: int
    test_schema: str  # DDL statements to create tables
    test_data: str    # DML statements to populate data
    expected_result: List[List[Any]]  # Expected query results
    description: Optional[str] = None
    max_execution_time: int = 30  # seconds
    
    def __post_init__(self):
        """Validation after initialization"""
        if not self.test_schema.strip():
            raise ValueError("test_schema cannot be empty")
        if not self.test_data.strip():
            raise ValueError("test_data cannot be empty")
        if not isinstance(self.expected_result, list):
            raise ValueError("expected_result must be a list")
        if self.max_execution_time <= 0:
            raise ValueError("max_execution_time must be positive")

@dataclass
class Challenge(BaseModel):
    """SQL Challenge with multiple test cases"""
    id: int
    title: str
    description: str
    difficulty: str  # "easy", "medium", "hard"
    test_cases: List[TestCase]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    max_query_results: int = 1000  # Row limit per query
    time_limit: int = 300  # Time limit in seconds
    points: int = 10  # Points awarded for correct solution
    category: Optional[str] = None  # e.g., "joins", "aggregation", "subqueries"
    
    def __post_init__(self):
        """Validation after initialization"""
        if not self.title.strip():
            raise ValueError("Challenge title cannot be empty")
        if not self.description.strip():
            raise ValueError("Challenge description cannot be empty")
        if self.difficulty not in ["easy", "medium", "hard"]:
            raise ValueError("Difficulty must be easy, medium, or hard")
        if not self.test_cases:
            raise ValueError("Challenge must have at least one test case")
        if self.max_query_results <= 0 or self.max_query_results > 10000:
            raise ValueError("max_query_results must be between 1 and 10000")
        if self.points <= 0:
            raise ValueError("Points must be positive")
        
        # Validate all test cases
        for i, test_case in enumerate(self.test_cases):
            try:
                test_case.validate()
            except ValueError as e:
                raise ValueError(f"Test case {i+1} validation failed: {e}")
    
    def get_test_case(self, test_id: int) -> Optional[TestCase]:
        """Get specific test case by ID"""
        return next((tc for tc in self.test_cases if tc.test_id == test_id), None)
    
    def add_test_case(self, test_case: TestCase):
        """Add a new test case"""
        # Ensure unique test IDs
        if any(tc.test_id == test_case.test_id for tc in self.test_cases):
            raise ValueError(f"Test case with ID {test_case.test_id} already exists")
        self.test_cases.append(test_case)
        self.updated_at = datetime.now()
