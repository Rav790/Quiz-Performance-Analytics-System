"""
schema.py - Collection Creation with Validation and Indexes
=============================================================
Creates the three collections (students, questions, attempts) with:
  - $jsonSchema validators for strict data integrity
  - Useful indexes for query performance
  - Idempotent behavior: safe to run multiple times

Usage:
    python schema.py           # Create collections (skip if they exist)
    python schema.py --reset   # Drop and recreate all collections

Design notes:
  - validationLevel="strict" means EVERY insert/update is checked
  - validationAction="error" means invalid documents are REJECTED (not just warned)
"""

import sys
from pymongo.errors import CollectionInvalid
from config import get_database


# ============================================================
# JSON Schema Validators
# ============================================================

STUDENTS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "Student Validation",
        "required": ["roll_no", "name", "email", "branch", "semester", "is_active", "created_at"],
        "properties": {
            "roll_no": {
                "bsonType": "string",
                "description": "Unique roll number like LPU2026001"
            },
            "name": {
                "bsonType": "string",
                "minLength": 2,
                "description": "Student full name"
            },
            "email": {
                "bsonType": "string",
                "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                "description": "Valid email address"
            },
            "branch": {
                "bsonType": "string",
                "enum": ["CSE", "IT", "ECE", "ME", "CIVIL"],
                "description": "Department/branch of study"
            },
            "semester": {
                "bsonType": "int",
                "minimum": 1,
                "maximum": 8,
                "description": "Current semester (1-8)"
            },
            "is_active": {
                "bsonType": "bool",
                "description": "Whether the student is currently active"
            },
            "created_at": {
                "bsonType": "date",
                "description": "Account creation timestamp"
            }
        }
    }
}

QUESTIONS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "Question Validation",
        "required": ["topic", "difficulty", "text", "options", "correct_option", "marks", "created_at"],
        "properties": {
            "topic": {
                "bsonType": "string",
                "enum": ["DBMS", "DSA", "OS", "Networks", "Python"],
                "description": "Subject topic"
            },
            "difficulty": {
                "bsonType": "string",
                "enum": ["easy", "medium", "hard"],
                "description": "Difficulty level"
            },
            "text": {
                "bsonType": "string",
                "minLength": 10,
                "description": "The question text"
            },
            "options": {
                "bsonType": "array",
                "minItems": 4,
                "maxItems": 4,
                "items": {
                    "bsonType": "object",
                    "required": ["key", "text"],
                    "properties": {
                        "key": {
                            "bsonType": "string",
                            "enum": ["A", "B", "C", "D"]
                        },
                        "text": {
                            "bsonType": "string"
                        }
                    }
                },
                "description": "Exactly 4 answer options (A, B, C, D)"
            },
            "correct_option": {
                "bsonType": "string",
                "enum": ["A", "B", "C", "D"],
                "description": "The correct answer key"
            },
            "marks": {
                "bsonType": "int",
                "minimum": 1,
                "description": "Points awarded for correct answer (minimum 1)"
            },
            "tags": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
                "description": "Optional tags for categorization"
            },
            "created_at": {
                "bsonType": "date",
                "description": "Question creation timestamp"
            }
        }
    }
}

ATTEMPTS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "Attempt Validation",
        "required": [
            "student_id", "quiz_title", "attempted_at",
            "time_taken_sec", "total_questions", "correct_count",
            "score_percent", "answers"
        ],
        "properties": {
            "student_id": {
                "bsonType": "objectId",
                "description": "Reference to students._id"
            },
            "quiz_title": {
                "bsonType": "string",
                "description": "Name of the quiz"
            },
            "attempted_at": {
                "bsonType": "date",
                "description": "When the quiz was taken"
            },
            "time_taken_sec": {
                "bsonType": "int",
                "minimum": 0,
                "description": "Total time in seconds"
            },
            "total_questions": {
                "bsonType": "int",
                "minimum": 1,
                "description": "Number of questions in the quiz"
            },
            "correct_count": {
                "bsonType": "int",
                "minimum": 0,
                "description": "Number of correct answers"
            },
            "score_percent": {
                "bsonType": "double",
                "minimum": 0,
                "maximum": 100,
                "description": "Score as percentage (0-100)"
            },
            "answers": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["question_id", "topic", "difficulty", "selected_option", "is_correct", "time_spent_sec"],
                    "properties": {
                        "question_id": {
                            "bsonType": "objectId",
                            "description": "Reference to questions._id"
                        },
                        "topic": {
                            "bsonType": "string",
                            "enum": ["DBMS", "DSA", "OS", "Networks", "Python"]
                        },
                        "difficulty": {
                            "bsonType": "string",
                            "enum": ["easy", "medium", "hard"]
                        },
                        "selected_option": {
                            # Allow string (A/B/C/D) or null (unanswered)
                            "bsonType": ["string", "null"]
                        },
                        "is_correct": {
                            "bsonType": "bool"
                        },
                        "time_spent_sec": {
                            "bsonType": "int",
                            "minimum": 0
                        }
                    }
                },
                "description": "Array of answer documents (embedded)"
            }
        }
    }
}


# ============================================================
# Collection + Index Creation
# ============================================================

def create_collections(db, reset=False):
    """
    Create all three collections with their $jsonSchema validators.
    
    If reset=True, drops existing collections first (destructive!).
    If reset=False, skips collections that already exist.
    
    mongosh equivalent:
        db.createCollection("students", {
            validator: { $jsonSchema: { ... } },
            validationLevel: "strict",
            validationAction: "error"
        })
    """
    collections_config = [
        ("students", STUDENTS_SCHEMA),
        ("questions", QUESTIONS_SCHEMA),
        ("attempts", ATTEMPTS_SCHEMA),
    ]

    existing = db.list_collection_names()

    for name, validator in collections_config:
        if reset and name in existing:
            db.drop_collection(name)
            print(f"  [DROPPED] {name}")
            existing.remove(name)

        if name in existing:
            print(f"  [SKIP] {name} already exists")
        else:
            db.create_collection(
                name,
                validator=validator,
                validationLevel="strict",
                validationAction="error"
            )
            print(f"  [CREATED] {name} with $jsonSchema validation")


def create_indexes(db):
    """
    Create indexes for query performance.

    Why each index:
      - students.roll_no (unique): fast lookup by roll number, prevents duplicates
      - students.email (unique): fast lookup by email, prevents duplicates
      - questions (topic, difficulty): most queries filter by topic and/or difficulty
      - attempts (student_id, attempted_at desc): get a student's recent attempts quickly
      - attempts (attempted_at): time-range queries across all attempts

    mongosh equivalent:
        db.students.createIndex({ roll_no: 1 }, { unique: true })
        db.students.createIndex({ email: 1 }, { unique: true })
        db.questions.createIndex({ topic: 1, difficulty: 1 })
        db.attempts.createIndex({ student_id: 1, attempted_at: -1 })
        db.attempts.createIndex({ attempted_at: 1 })
    """
    # Students indexes
    db.students.create_index("roll_no", unique=True, name="idx_roll_no_unique")
    db.students.create_index("email", unique=True, name="idx_email_unique")
    print("  [INDEX] students: roll_no (unique), email (unique)")

    # Questions compound index — most queries filter on topic + difficulty together
    db.questions.create_index(
        [("topic", 1), ("difficulty", 1)],
        name="idx_topic_difficulty"
    )
    print("  [INDEX] questions: (topic, difficulty)")

    # Attempts — compound index for "get student's recent attempts" pattern
    db.attempts.create_index(
        [("student_id", 1), ("attempted_at", -1)],
        name="idx_student_attempts"
    )
    # Attempts — single index for date-range queries
    db.attempts.create_index("attempted_at", name="idx_attempted_at")
    print("  [INDEX] attempts: (student_id, attempted_at desc), attempted_at")


def modify_validator_example(db):
    """
    Demonstrate how to modify a validator on an existing collection
    using the collMod command. This adds a maximum length check on student names.

    mongosh equivalent:
        db.runCommand({
            collMod: "students",
            validator: { ... updated schema ... },
            validationLevel: "strict"
        })
    """
    # Make a copy of the schema and add a maxLength to name
    updated_schema = STUDENTS_SCHEMA.copy()
    updated_schema["$jsonSchema"]["properties"]["name"]["maxLength"] = 100

    db.command({
        "collMod": "students",
        "validator": updated_schema,
        "validationLevel": "strict",
        "validationAction": "error"
    })
    print("  [MODIFIED] students validator: added name maxLength=100")


def setup_database(db, reset=False):
    """
    Full setup: create collections with validation, then create indexes.
    This is the main entry point called by other scripts.
    """
    print("\n=== Database Schema Setup ===")
    create_collections(db, reset=reset)

    print("\n=== Creating Indexes ===")
    create_indexes(db)

    print("\n=== Schema setup complete ===\n")


if __name__ == "__main__":
    # Check for --reset flag
    reset = "--reset" in sys.argv

    if reset:
        print("[!] RESET MODE: All collections will be dropped and recreated!")

    db = get_database()
    setup_database(db, reset=reset)

    # Demonstrate modifying a validator
    print("\n=== Validator Modification Demo ===")
    modify_validator_example(db)
