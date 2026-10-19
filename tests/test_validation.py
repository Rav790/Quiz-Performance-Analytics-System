"""
tests/test_validation.py - Validation Rule Tests
====================================================
Tests that the $jsonSchema validators correctly reject invalid documents
and accept valid ones.

Tests 6 invalid document insertions:
  1. Bad email format
  2. Semester out of range (12)
  3. Score percent out of range (150)
  4. Invalid topic enum
  5. Only 3 options (needs exactly 4)
  6. Missing required field

Plus 1 valid insert that should succeed.

Usage:
    python tests/test_validation.py
"""

import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from bson import ObjectId
from pymongo.errors import WriteError
from config import get_database


def test_invalid_documents(db):
    """
    Try to insert invalid documents and verify they are rejected.
    Each test catches WriteError and prints the validation error message.
    """
    print("\n=== Validation Tests: Invalid Documents ===\n")
    passed = 0
    failed = 0

    # ---- Test 1: Bad email format ----
    print("Test 1: Bad email format (missing @)")
    try:
        db.students.insert_one({
            "roll_no": "TEST001",
            "name": "Test User",
            "email": "invalid-email-no-at-sign",  # Missing @ sign
            "branch": "CSE",
            "semester": 5,
            "is_active": True,
            "created_at": datetime.now()
        })
        print("  FAIL: Document was accepted (should have been rejected)")
        failed += 1
    except WriteError as e:
        print(f"  PASS: Rejected - {e.details.get('errmsg', str(e))[:100]}")
        passed += 1

    # ---- Test 2: Semester out of range ----
    print("\nTest 2: Semester = 12 (max is 8)")
    try:
        db.students.insert_one({
            "roll_no": "TEST002",
            "name": "Test User",
            "email": "test002@lpu.in",
            "branch": "CSE",
            "semester": 12,  # Maximum is 8
            "is_active": True,
            "created_at": datetime.now()
        })
        print("  FAIL: Document was accepted (should have been rejected)")
        failed += 1
    except WriteError as e:
        print(f"  PASS: Rejected - {e.details.get('errmsg', str(e))[:100]}")
        passed += 1

    # ---- Test 3: Score percent > 100 ----
    print("\nTest 3: Score percent = 150 (max is 100)")
    try:
        db.attempts.insert_one({
            "student_id": ObjectId(),
            "quiz_title": "Test Quiz",
            "attempted_at": datetime.now(),
            "time_taken_sec": 100,
            "total_questions": 10,
            "correct_count": 7,
            "score_percent": 150.0,  # Maximum is 100
            "answers": []
        })
        print("  FAIL: Document was accepted (should have been rejected)")
        failed += 1
    except WriteError as e:
        print(f"  PASS: Rejected - {e.details.get('errmsg', str(e))[:100]}")
        passed += 1

    # ---- Test 4: Invalid topic enum ----
    print("\nTest 4: Invalid topic 'Biology' (not in enum)")
    try:
        db.questions.insert_one({
            "topic": "Biology",  # Not in [DBMS, DSA, OS, Networks, Python]
            "difficulty": "easy",
            "text": "What is photosynthesis?",
            "options": [
                {"key": "A", "text": "A"},
                {"key": "B", "text": "B"},
                {"key": "C", "text": "C"},
                {"key": "D", "text": "D"}
            ],
            "correct_option": "A",
            "marks": 1,
            "tags": [],
            "created_at": datetime.now()
        })
        print("  FAIL: Document was accepted (should have been rejected)")
        failed += 1
    except WriteError as e:
        print(f"  PASS: Rejected - {e.details.get('errmsg', str(e))[:100]}")
        passed += 1

    # ---- Test 5: Only 3 options (needs exactly 4) ----
    print("\nTest 5: Only 3 options (minItems is 4)")
    try:
        db.questions.insert_one({
            "topic": "DBMS",
            "difficulty": "easy",
            "text": "Some question about databases for testing validation",
            "options": [
                {"key": "A", "text": "Option A"},
                {"key": "B", "text": "Option B"},
                {"key": "C", "text": "Option C"}
                # Missing option D!
            ],
            "correct_option": "A",
            "marks": 1,
            "tags": [],
            "created_at": datetime.now()
        })
        print("  FAIL: Document was accepted (should have been rejected)")
        failed += 1
    except WriteError as e:
        print(f"  PASS: Rejected - {e.details.get('errmsg', str(e))[:100]}")
        passed += 1

    # ---- Test 6: Missing required field (name) ----
    print("\nTest 6: Missing required field 'name'")
    try:
        db.students.insert_one({
            "roll_no": "TEST006",
            # "name" is missing!
            "email": "test006@lpu.in",
            "branch": "CSE",
            "semester": 6,
            "is_active": True,
            "created_at": datetime.now()
        })
        print("  FAIL: Document was accepted (should have been rejected)")
        failed += 1
    except WriteError as e:
        print(f"  PASS: Rejected - {e.details.get('errmsg', str(e))[:100]}")
        passed += 1

    print(f"\n--- Invalid Document Tests: {passed} passed, {failed} failed ---")
    return passed, failed


def test_valid_document(db):
    """
    Insert a valid document to confirm the validator doesn't reject good data.
    Cleans up after itself by deleting the test document.
    """
    print("\n=== Validation Test: Valid Document ===\n")

    doc = {
        "roll_no": "TEST_VALID_001",
        "name": "Valid Student",
        "email": "valid.student@lpu.in",
        "branch": "IT",
        "semester": 6,
        "is_active": True,
        "created_at": datetime.now()
    }

    try:
        result = db.students.insert_one(doc)
        print(f"  PASS: Valid document accepted (ID: {result.inserted_id})")

        # Clean up: remove the test document
        db.students.delete_one({"_id": result.inserted_id})
        print("  (Cleaned up test document)")
        return True
    except WriteError as e:
        print(f"  FAIL: Valid document was rejected: {e}")
        return False


def run_all_validation_tests(db):
    """Run all validation tests and return a summary."""
    invalid_passed, invalid_failed = test_invalid_documents(db)
    valid_ok = test_valid_document(db)

    total_passed = invalid_passed + (1 if valid_ok else 0)
    total_failed = invalid_failed + (0 if valid_ok else 1)

    print(f"\n{'='*50}")
    print(f"  VALIDATION TEST SUMMARY: {total_passed}/{total_passed + total_failed} passed")
    print(f"{'='*50}\n")

    return total_passed, total_failed


if __name__ == "__main__":
    db = get_database()
    run_all_validation_tests(db)
