"""
main.py - Interactive Menu-Driven CLI
========================================
Ties all modules together in a user-friendly menu interface.

Sections:
  1) Setup (create schema / seed / reset)
  2) Student CRUD
  3) Question CRUD
  4) Attempts (record, view, delete)
  5) Analytics (aggregation pipelines)
  6) Validation demo
  0) Exit

Usage:
    python main.py
"""

import sys
from datetime import datetime, timedelta
from bson import ObjectId
from config import get_database
from schema import setup_database
from seed_data import seed_database
from crud_operations import (
    add_student, find_student_by_roll, search_students_by_name,
    update_student_semester, deactivate_students_of_branch,
    upsert_student, list_questions, add_tag_to_question,
    increment_marks_for_hard_questions, delete_question,
    get_student_attempts, delete_old_attempts,
    count_documents_examples, query_with_operators,
    delete_student_with_attempts
)
from aggregations import (
    topic_wise_accuracy, leaderboard, avg_time_by_difficulty,
    monthly_trend, weakest_topic_per_student, hardest_questions,
    score_distribution, student_dashboard, pass_fail_labeling,
    rank_students
)
from tests.test_validation import run_all_validation_tests


def print_menu():
    """Print the main menu."""
    print("\n" + "=" * 55)
    print("  QUIZ PERFORMANCE ANALYTICS SYSTEM")
    print("=" * 55)
    print("  1) Setup & Data")
    print("  2) Student Operations")
    print("  3) Question Operations")
    print("  4) Attempt Operations")
    print("  5) Analytics (Aggregation Pipelines)")
    print("  6) Validation Demo")
    print("  0) Exit")
    print("-" * 55)


def setup_menu(db):
    """Sub-menu for setup operations."""
    while True:
        print("\n--- Setup & Data ---")
        print("  1) Create schema (skip if exists)")
        print("  2) Seed database (reset + create + seed)")
        print("  3) Reset only (drop all collections)")
        print("  4) Show collection counts")
        print("  0) Back")

        choice = input("\nChoice: ").strip()

        if choice == "1":
            setup_database(db, reset=False)
        elif choice == "2":
            setup_database(db, reset=True)
            seed_database(db)
        elif choice == "3":
            setup_database(db, reset=True)
        elif choice == "4":
            print(f"\n  students:  {db.students.count_documents({})}")
            print(f"  questions: {db.questions.count_documents({})}")
            print(f"  attempts:  {db.attempts.count_documents({})}")
        elif choice == "0":
            break
        else:
            print("  Invalid choice. Try again.")


def student_menu(db):
    """Sub-menu for student CRUD operations."""
    while True:
        print("\n--- Student Operations ---")
        print("  1) Add student")
        print("  2) Find by roll number")
        print("  3) Search by name")
        print("  4) Update semester")
        print("  5) Deactivate branch")
        print("  6) Upsert student")
        print("  7) Delete student (with attempts)")
        print("  8) Count & query operator examples")
        print("  0) Back")

        choice = input("\nChoice: ").strip()

        if choice == "1":
            roll = input("  Roll No: ").strip()
            name = input("  Name: ").strip()
            email = input("  Email: ").strip()
            branch = input("  Branch (CSE/IT/ECE/ME/CIVIL): ").strip().upper()
            try:
                sem = int(input("  Semester (1-8): ").strip())
            except ValueError:
                print("  Invalid semester.")
                continue
            add_student(db, roll, name, email, branch, sem)

        elif choice == "2":
            roll = input("  Roll No: ").strip()
            find_student_by_roll(db, roll)

        elif choice == "3":
            pattern = input("  Name pattern (regex): ").strip()
            search_students_by_name(db, pattern)

        elif choice == "4":
            roll = input("  Roll No: ").strip()
            try:
                sem = int(input("  New Semester: ").strip())
            except ValueError:
                print("  Invalid semester.")
                continue
            update_student_semester(db, roll, sem)

        elif choice == "5":
            branch = input("  Branch to deactivate: ").strip().upper()
            deactivate_students_of_branch(db, branch)

        elif choice == "6":
            roll = input("  Roll No: ").strip()
            name = input("  Name: ").strip()
            email = input("  Email: ").strip()
            branch = input("  Branch: ").strip().upper()
            try:
                sem = int(input("  Semester: ").strip())
            except ValueError:
                print("  Invalid semester.")
                continue
            upsert_student(db, roll, name, email, branch, sem)

        elif choice == "7":
            roll = input("  Roll No to delete: ").strip()
            student = db.students.find_one({"roll_no": roll})
            if student:
                delete_student_with_attempts(db, student["_id"])
            else:
                print(f"  Student {roll} not found.")

        elif choice == "8":
            count_documents_examples(db)
            query_with_operators(db)

        elif choice == "0":
            break
        else:
            print("  Invalid choice. Try again.")


def question_menu(db):
    """Sub-menu for question operations."""
    while True:
        print("\n--- Question Operations ---")
        print("  1) List questions (with filter)")
        print("  2) Add tag to a question")
        print("  3) Increment marks for hard questions")
        print("  4) Delete a question")
        print("  0) Back")

        choice = input("\nChoice: ").strip()

        if choice == "1":
            topic = input("  Topic (DBMS/DSA/OS/Networks/Python or blank): ").strip() or None
            diff = input("  Difficulty (easy/medium/hard or blank): ").strip() or None
            try:
                limit = int(input("  Limit (default 10): ").strip() or "10")
            except ValueError:
                limit = 10
            list_questions(db, topic=topic, difficulty=diff, limit=limit)

        elif choice == "2":
            # Show a question to tag
            q = db.questions.find_one()
            if q:
                print(f"  Question: {q['text'][:60]}...")
                tag = input("  Tag to add: ").strip()
                add_tag_to_question(db, q["_id"], tag)
            else:
                print("  No questions found.")

        elif choice == "3":
            increment_marks_for_hard_questions(db)

        elif choice == "4":
            # Show first question to confirm
            q = db.questions.find_one()
            if q:
                print(f"  Will delete: {q['text'][:60]}...")
                confirm = input("  Confirm? (y/n): ").strip().lower()
                if confirm == "y":
                    delete_question(db, q["_id"])
            else:
                print("  No questions found.")

        elif choice == "0":
            break
        else:
            print("  Invalid choice. Try again.")


def attempt_menu(db):
    """Sub-menu for attempt operations."""
    while True:
        print("\n--- Attempt Operations ---")
        print("  1) View student's attempts")
        print("  2) Delete old attempts")
        print("  0) Back")

        choice = input("\nChoice: ").strip()

        if choice == "1":
            roll = input("  Student Roll No: ").strip()
            student = db.students.find_one({"roll_no": roll})
            if student:
                get_student_attempts(db, student["_id"])
            else:
                print(f"  Student {roll} not found.")

        elif choice == "2":
            days = input("  Delete attempts older than (days): ").strip()
            try:
                days = int(days)
                before = datetime.now() - timedelta(days=days)
                delete_old_attempts(db, before)
            except ValueError:
                print("  Invalid number of days.")

        elif choice == "0":
            break
        else:
            print("  Invalid choice. Try again.")


def analytics_menu(db):
    """Sub-menu for running aggregation pipelines."""
    while True:
        print("\n--- Analytics (Aggregation Pipelines) ---")
        print("  1) Topic-wise accuracy")
        print("  2) Leaderboard (top 10)")
        print("  3) Avg time per question by difficulty")
        print("  4) Monthly attempts trend")
        print("  5) Weakest topic per student")
        print("  6) Hardest questions")
        print("  7) Score distribution")
        print("  8) Student dashboard")
        print("  9) Pass/Fail labeling")
        print(" 10) Student rankings ($setWindowFields)")
        print("  0) Back")

        choice = input("\nChoice: ").strip()

        if choice == "1":
            topic_wise_accuracy(db)
        elif choice == "2":
            leaderboard(db)
        elif choice == "3":
            avg_time_by_difficulty(db)
        elif choice == "4":
            monthly_trend(db)
        elif choice == "5":
            weakest_topic_per_student(db)
        elif choice == "6":
            hardest_questions(db)
        elif choice == "7":
            score_distribution(db)
        elif choice == "8":
            roll = input("  Student Roll No: ").strip()
            student_dashboard(db, roll)
        elif choice == "9":
            pass_fail_labeling(db)
        elif choice == "10":
            rank_students(db)
        elif choice == "0":
            break
        else:
            print("  Invalid choice. Try again.")


def main():
    """Main entry point for the CLI application."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("\n=== Quiz Performance Analytics System ===")
    print("   CSE494 - Intelligent NoSQL Databases\n")

    db = get_database()

    while True:
        print_menu()
        choice = input("Choice: ").strip()

        if choice == "1":
            setup_menu(db)
        elif choice == "2":
            student_menu(db)
        elif choice == "3":
            question_menu(db)
        elif choice == "4":
            attempt_menu(db)
        elif choice == "5":
            analytics_menu(db)
        elif choice == "6":
            run_all_validation_tests(db)
        elif choice == "0":
            print("\nGoodbye!")
            sys.exit(0)
        else:
            print("  Invalid choice. Please enter 0-6.")


if __name__ == "__main__":
    main()
