"""
Database utilities for managing challenges and data persistence
"""

import json
import sqlite3
import time
import re
import signal
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from .challenge import Challenge, TestCase
from contextlib import contextmanager
from ..models.submission import TestCaseResult, SubmissionStatus

class DatabaseManager:
    """Manages database operations and data loading"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        app.db_manager = self

class ChallengeLoader:
    """Loads challenges from JSON or database"""
    
    @staticmethod
    def load_from_json(json_file_path: Path) -> List[Challenge]:
        """Load challenges from JSON file"""
        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            challenges = []
            for challenge_data in data.get('challenges', []):
                test_cases = []
                for tc_data in challenge_data.get('test_cases', []):
                    test_case = TestCase(
                        test_id=tc_data['test_id'],
                        test_schema=tc_data['test_schema'],
                        test_data=tc_data['test_data'],
                        expected_result=tc_data['expected_result'],
                        description=tc_data.get('description'),
                        max_execution_sec=tc_data.get('max_execution_time', 30)
                    )
                    test_cases.append(test_case)
                
                challenge = Challenge(
                    id=challenge_data['id'],
                    title=challenge_data['title'],
                    description=challenge_data['description'],
                    difficulty=challenge_data['difficulty'],
                    test_cases=test_cases,
                    category=challenge_data.get('category'),
                    points=challenge_data.get('points', 10)
                )
                challenges.append(challenge)
            
            return challenges
           
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Error loading challenges from JSON: {e}")
    
    @staticmethod
    def load_challenge_from_json(json_file_path: Path, challenge_id: int) -> Challenge:
        """Load a single challenge from JSON file"""
        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)

            for challenge_data in data.get('challenges', []):
                if challenge_data['id'] == challenge_id:
                    test_cases = []
                    for tc_data in challenge_data.get('test_cases', []):
                        test_case = TestCase(
                            test_id=tc_data['test_id'],
                            test_schema=tc_data['test_schema'],
                            test_data=tc_data['test_data'],
                            expected_result=tc_data['expected_result'],
                            description=tc_data.get('description'),
                            max_execution_sec=tc_data.get('max_execution_time', 30)
                        )
                        test_cases.append(test_case)

                    challenge = Challenge(
                        id=challenge_data['id'],
                        title=challenge_data['title'],
                        description=challenge_data['description'],
                        difficulty=challenge_data['difficulty'],
                        test_cases=test_cases,
                        category=challenge_data.get('category'),
                        points=challenge_data.get('points', 10)
                    )
                    return challenge
                
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Error loading challenge from JSON: {e}")
        

    @staticmethod
    def save_to_json(challenges: List[Challenge], json_file_path: Path):
        """Save challenges to JSON file"""
        data = {
            'challenges': [challenge.to_dict() for challenge in challenges]
        }
        
        with open(json_file_path, 'w') as f:
            json.dump(data, f, indent=2)


def eval_sql_with_defog(challenge: Challenge, sql_query: str, max_rows: int = 1000) -> Tuple[bool, str, List[TestCaseResult]]:
    """
    Executes defog-style evaluation across all test cases.
    Returns (passed: bool, feedback_msg: str, test_results: List[TestCaseResult])
    """
    
    # Input validation
    if not sql_query or not sql_query.strip():
        return False, "SQL query cannot be empty", []
    
    sql_query = sql_query.strip()
    
    # Security check - only SELECT allowed (improved validation)
    if not _is_select_only_query(sql_query):
        return False, "Only SELECT statements are allowed", []
    
    # Additional security - check for dangerous patterns
    if _contains_dangerous_patterns(sql_query):
        return False, "Query contains potentially dangerous operations", []
    
    test_results = []
    all_passed = True
    feedback_messages = []
    
    # Process each test case
    for i, test_case in enumerate(challenge.test_cases):
        start_time = time.perf_counter()
        
        try:
            # Execute with timeout protection
            with _query_timeout(test_case.max_execution_sec):
                result = _execute_test_case(test_case, sql_query, max_rows)
                print(f'qeury result {result}')
            execution_time = time.perf_counter() - start_time
            
            if result['success']:
                # Compare results using Defog-style comparison
                is_correct = _compare_results(
                    result['actual_result'], 
                    test_case.expected_result,
                    exact_match=True
                )
                
                if is_correct:
                    test_result = TestCaseResult(
                        test_id=test_case.test_id,
                        status=SubmissionStatus.CORRECT,
                        execution_time=execution_time,
                        actual_result=result['actual_result'],
                        rows_returned=len(result['actual_result'])
                    )
                    feedback_messages.append(f"✓ Test case {i+1}: Passed")
                else:
                    # Try subset match (Defog's fallback approach)
                    is_subset = _compare_results(
                        result['actual_result'], 
                        test_case.expected_result,
                        exact_match=False
                    )
                    
                    if is_subset:
                        test_result = TestCaseResult(
                            test_id=test_case.test_id,
                            status=SubmissionStatus.CORRECT,
                            execution_time=execution_time,
                            actual_result=result['actual_result'],
                            rows_returned=len(result['actual_result'])
                        )
                        feedback_messages.append(f"✓ Test case {i+1}: Passed (subset match)")
                    else:
                        test_result = TestCaseResult(
                            test_id=test_case.test_id,
                            status=SubmissionStatus.INCORRECT,
                            execution_time=execution_time,
                            actual_result=result['actual_result'],
                            error_message=f"Expected: {test_case.expected_result}, Got: {result['actual_result']}",
                            rows_returned=len(result['actual_result'])
                        )
                        feedback_messages.append(f"✗ Test case {i+1}: Failed - Result mismatch")
                        all_passed = False
            else:
                # Query execution failed
                test_result = TestCaseResult(
                    test_id=test_case.test_id,
                    status=SubmissionStatus.ERROR,
                    execution_time=execution_time,
                    error_message=result['error'],
                    rows_returned=0
                )
                feedback_messages.append(f"✗ Test case {i+1}: Error - {result['error']}")
                all_passed = False
                
        except TimeoutError:
            test_result = TestCaseResult(
                test_id=test_case.test_id,
                status=SubmissionStatus.TIMEOUT,
                execution_time=test_case.max_execution_sec,
                error_message=f"Query exceeded time limit of {test_case.max_execution_sec} seconds",
                rows_returned=0
            )
            feedback_messages.append(f"✗ Test case {i+1}: Timeout")
            all_passed = False
            
        except Exception as e:
            test_result = TestCaseResult(
                test_id=test_case.test_id,
                status=SubmissionStatus.ERROR,
                execution_time=time.perf_counter() - start_time,
                error_message=f"Unexpected error: {str(e)}",
                rows_returned=0
            )
            feedback_messages.append(f"✗ Test case {i+1}: System error")
            all_passed = False
        
        test_results.append(test_result)
    
    # Generate overall feedback
    passed_count = sum(1 for r in test_results if r.status == SubmissionStatus.CORRECT)
    total_count = len(test_results)
    
    if all_passed:
        overall_feedback = f"All tests passed! ({passed_count}/{total_count})"
    else:
        overall_feedback = f"Tests passed: {passed_count}/{total_count}"
    
    detailed_feedback = f"{overall_feedback}\n" + "\n".join(feedback_messages)
    
    return all_passed, detailed_feedback, test_results

def _is_select_only_query(sql_query: str) -> bool:
    """
    Validate that the query contains only SELECT statements.
    Uses basic parsing to handle comments and whitespace.
    """
    # Remove comments and normalize whitespace
    query_clean = _remove_sql_comments(sql_query.upper().strip())
    
    # Split by semicolon to handle multiple statements
    statements = [stmt.strip() for stmt in query_clean.split(';') if stmt.strip()]
    
    # Check each statement starts with SELECT
    for statement in statements:
        if not statement.startswith('SELECT'):
            return False
    
    return True


def _remove_sql_comments(sql: str) -> str:
    """Remove SQL comments from query string."""
    # Remove single-line comments (-- style)
    sql = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
    
    # Remove multi-line comments (/* */ style)
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    
    return sql.strip()


def _contains_dangerous_patterns(sql_query: str) -> bool:
    """
    Check for potentially dangerous SQL patterns even in SELECT statements.
    """
    dangerous_patterns = [
        r'\bDROP\b', r'\bDELETE\b', r'\bINSERT\b', r'\bUPDATE\b',
        r'\bCREATE\b', r'\bALTER\b', r'\bTRUNCATE\b', r'\bEXEC\b',
        r'\bEXECUTE\b', r'\bxp_\b', r'\bsp_\b', r';\s*\w+',  # Multiple statements
        r'\bINTO\s+OUTFILE\b', r'\bLOAD_FILE\b'  # File operations
    ]
    
    query_upper = sql_query.upper()
    for pattern in dangerous_patterns:
        if re.search(pattern, query_upper):
            return True
    
    return False


@contextmanager
def _query_timeout(seconds: int):
    """
    Context manager: times out after 'seconds' (SIGALRM on Unix; disabled on Windows).
    """
    # Only use SIGALRM if available (i.e., not on Windows)
    if hasattr(signal, "SIGALRM") and platform.system() != "Windows":
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Query execution exceeded {seconds} seconds (SIGALRM)")
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # No timeout enforcement on Windows; just yield.
        yield


def _execute_test_case(test_case: TestCase, sql_query: str, max_rows: int) -> dict:
    """
    Execute SQL query against a single test case in an isolated in-memory database.
    Returns dict with success status, actual results, or error message.
    """
    conn = None
    cursor = None
    
    try:
        # Create isolated in-memory database
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        
        # Set up the test environment
        cursor.executescript(test_case.test_schema)
        cursor.executescript(test_case.test_data)
        
        # Execute the user's query
        cursor.execute(sql_query)
        raw_results = cursor.fetchall()
        
        # Check row limit
        if len(raw_results) > max_rows:
            return {
                'success': False,
                'error': f"Query returned {len(raw_results)} rows, exceeding limit of {max_rows}"
            }
        
        # Convert results to consistent format
        actual_result = [list(row) for row in raw_results] if raw_results else []
        
        return {
            'success': True,
            'actual_result': actual_result
        }
        
    except sqlite3.Error as e:
        return {
            'success': False,
            'error': f"SQL Error: {str(e)}"
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Execution Error: {str(e)}"
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _compare_results(actual: List[List[Any]], expected: List[List[Any]], exact_match: bool = True) -> bool:
    """
    Compare query results using Defog-style comparison logic.
    
    Args:
        actual: The actual query results
        expected: The expected results from test case
        exact_match: If True, require exact match. If False, allow subset match.
    
    Returns:
        bool: True if results match according to the specified criteria
    """
    if not actual and not expected:
        return True
    
    if not actual or not expected:
        return False
    
    # Normalize results - convert to comparable format
    actual_normalized = _normalize_result_set(actual)
    expected_normalized = _normalize_result_set(expected)
    
    if exact_match:
        # Exact match: same length and same content (order-independent)
        if len(actual_normalized) != len(expected_normalized):
            return False
        
        # Convert to sets of tuples for comparison (ignores order)
        actual_set = set(tuple(row) for row in actual_normalized)
        expected_set = set(tuple(row) for row in expected_normalized)
        
        return actual_set == expected_set
    
    else:
        # Subset match: check if expected is subset of actual
        expected_set = set(tuple(row) for row in expected_normalized)
        actual_set = set(tuple(row) for row in actual_normalized)
        
        return expected_set.issubset(actual_set)


def _normalize_result_set(results: List[List[Any]]) -> List[List[Any]]:
    """
    Normalize result set for comparison by handling data types consistently.
    """
    normalized = []
    
    for row in results:
        normalized_row = []
        for value in row:
            # Handle None/NULL values
            if value is None:
                normalized_row.append(None)
            # Convert numbers to consistent format
            elif isinstance(value, (int, float)):
                # Handle floating point precision issues
                if isinstance(value, float) and value.is_integer():
                    normalized_row.append(int(value))
                else:
                    normalized_row.append(value)
            # Convert strings and handle case sensitivity
            elif isinstance(value, str):
                normalized_row.append(value.strip())
            else:
                # Keep other types as-is
                normalized_row.append(value)
        
        normalized.append(normalized_row)
    
    return normalized

