"""
demo_run.py - Non-Interactive Full Demo
==========================================
Runs every major operation in order and saves outputs to the outputs/ folder.
This is the script to run for screenshots and the project report.

Execution order:
  1. Reset + Schema creation + Seeding
  2. Validation tests
  3. CRUD operations (create, read, update, delete)
  4. All 8 aggregation pipelines + bonus
  5. explain() on an indexed query

Each section's output is written to outputs/NN_name.txt AND printed to console.

Usage:
    python demo_run.py
"""

import sys
import os
import io
from datetime import datetime, timedelta
from contextlib import redirect_stdout
from bson import ObjectId, json_util
import json

from config import get_database
from schema import setup_database, modify_validator_example
from seed_data import seed_database
from crud_operations import (
    add_student, find_student_by_roll, search_students_by_name,
    list_questions, get_student_attempts, count_documents_examples,
    query_with_operators, update_student_semester,
    deactivate_students_of_branch, add_tag_to_question,
    increment_marks_for_hard_questions, upsert_student,
    fix_attempt_answer, delete_question, delete_old_attempts,
    record_attempt
)
from aggregations import (
    topic_wise_accuracy, leaderboard, avg_time_by_difficulty,
    monthly_trend, weakest_topic_per_student, hardest_questions,
    score_distribution, student_dashboard, pass_fail_labeling,
    rank_students
)
from tests.test_validation import run_all_validation_tests


# ============================================================
# Ensure stdout supports unicode without crashing on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def run_section(name, filename, func, *args, **kwargs):
    """
    Run a function, capture its stdout output, print it, and save to file.
    """
    banner = f"\n{'#'*70}\n# {name}\n{'#'*70}\n"

    # Capture output
    captured = io.StringIO()
    result = None
    with redirect_stdout(captured):
        print(banner)
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            print(f"\n[ERROR] {e}")

    output = captured.getvalue()

    # Print to console (safely)
    try:
        sys.stdout.write(output)
    except UnicodeEncodeError:
        sys.stdout.write(output.encode("ascii", errors="replace").decode("ascii"))
    sys.stdout.flush()

    # Save to file
    filepath = os.path.join("outputs", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(output)

    return result


# ============================================================
# Main Demo Script
# ============================================================

def main():
    """Run the complete demo end to end."""
    print("=" * 70)
    print("  QUIZ PERFORMANCE ANALYTICS SYSTEM - FULL DEMO RUN")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Create outputs directory
    os.makedirs("outputs", exist_ok=True)

    # Connect to database
    db = get_database()

    # ============================================================
    # SECTION 1: Reset + Schema + Seed
    # ============================================================
    run_section(
        "SECTION 1: Database Setup & Seeding",
        "01_setup_and_seed.txt",
        lambda: (setup_database(db, reset=True), seed_database(db))
    )

    # ============================================================
    # SECTION 2: Validation Tests
    # ============================================================
    run_section(
        "SECTION 2: Validation Tests",
        "02_validation_tests.txt",
        run_all_validation_tests, db
    )

    # ============================================================
    # SECTION 3: CREATE Operations
    # ============================================================
    def demo_create():
        print("\n--- insert_one: Add a new student ---")
        add_student(db, "LPU2026031", "Demo Student", "demo.student@lpu.in", "CSE", 7)

        print("\n--- insert_one: Record a quiz attempt ---")
        student = db.students.find_one({"roll_no": "LPU2026001"})
        question = db.questions.find_one({"topic": "DBMS"})
        if student and question:
            answers = [
                {
                    "question_id": question["_id"],
                    "topic": question["topic"],
                    "difficulty": question["difficulty"],
                    "selected_option": "A",
                    "is_correct": True,
                    "time_spent_sec": 25
                }
            ]
            record_attempt(db, student["_id"], "Demo Quiz", answers)

    run_section(
        "SECTION 3: CREATE Operations",
        "03_create_operations.txt",
        demo_create
    )

    # ============================================================
    # SECTION 4: READ Operations
    # ============================================================
    def demo_read():
        print("\n--- findOne: Find student by roll number ---")
        find_student_by_roll(db, "LPU2026001")

        print("\n--- find: List DBMS questions ---")
        list_questions(db, topic="DBMS", limit=5)

        print("\n--- find: Search students by name ---")
        search_students_by_name(db, "sharma")

        print("\n--- find: Get student attempts ---")
        student = db.students.find_one({"roll_no": "LPU2026001"})
        if student:
            get_student_attempts(db, student["_id"])

        print("\n--- countDocuments examples ---")
        count_documents_examples(db)

        print("\n--- Query operators: $in, $gte/$lte, $and, $or ---")
        query_with_operators(db)

    run_section(
        "SECTION 4: READ Operations",
        "04_read_operations.txt",
        demo_read
    )

    # ============================================================
    # SECTION 5: UPDATE Operations
    # ============================================================
    def demo_update():
        print("\n--- $set: Update student semester ---")
        update_student_semester(db, "LPU2026001", 8)

        print("\n--- $set with updateMany: Deactivate ME students ---")
        deactivate_students_of_branch(db, "ME")

        print("\n--- $addToSet: Add tag to question ---")
        question = db.questions.find_one({"topic": "DBMS"})
        if question:
            add_tag_to_question(db, question["_id"], "important")

        print("\n--- $inc: Increment marks for hard questions ---")
        increment_marks_for_hard_questions(db)

        print("\n--- upsert: Upsert a student ---")
        upsert_student(db, "LPU2026032", "Upsert Student", "upsert@lpu.in", "IT", 6)

        print("\n--- arrayFilters: Fix an attempt answer ---")
        attempt = db.attempts.find_one()
        if attempt and attempt["answers"]:
            first_answer = attempt["answers"][0]
            fix_attempt_answer(
                db, attempt["_id"], first_answer["question_id"],
                "B", not first_answer["is_correct"]
            )

    run_section(
        "SECTION 5: UPDATE Operations",
        "05_update_operations.txt",
        demo_update
    )

    # ============================================================
    # SECTION 6: DELETE Operations
    # ============================================================
    def demo_delete():
        print("\n--- deleteOne: Delete a question ---")
        # Find a question that was just tagged (so we don't break seed data too much)
        question = db.questions.find_one({"tags": "important"})
        if question:
            delete_question(db, question["_id"])

        print("\n--- deleteMany: Delete attempts older than 170 days ---")
        cutoff = datetime.now() - timedelta(days=170)
        delete_old_attempts(db, cutoff)

    run_section(
        "SECTION 6: DELETE Operations",
        "06_delete_operations.txt",
        demo_delete
    )

    # ============================================================
    # SECTION 7: Aggregation Pipelines
    # ============================================================
    def demo_agg_1_to_4():
        topic_wise_accuracy(db)
        leaderboard(db)
        avg_time_by_difficulty(db)
        monthly_trend(db)

    run_section(
        "SECTION 7a: Aggregations 1-4",
        "07a_aggregations_1_to_4.txt",
        demo_agg_1_to_4
    )

    def demo_agg_5_to_8():
        weakest_topic_per_student(db)
        hardest_questions(db)
        score_distribution(db)
        student_dashboard(db, "LPU2026001")

    run_section(
        "SECTION 7b: Aggregations 5-8",
        "07b_aggregations_5_to_8.txt",
        demo_agg_5_to_8
    )

    def demo_agg_bonus():
        pass_fail_labeling(db)
        rank_students(db)

    run_section(
        "SECTION 7c: Bonus Aggregations",
        "07c_bonus_aggregations.txt",
        demo_agg_bonus
    )

    # ============================================================
    # SECTION 8: explain() on Indexed Query
    # ============================================================
    def demo_explain():
        """
        Use explain() to show that an indexed query uses IXSCAN (index scan)
        instead of COLLSCAN (full collection scan).
        
        We run explain on the student lookup by roll_no, which has a unique index.
        """
        print("\n--- explain() on indexed query: find student by roll_no ---")
        print("  Query: db.students.find({ roll_no: 'LPU2026001' })")
        print()

        # Run explain on an indexed query
        explain_result = db.students.find(
            {"roll_no": "LPU2026001"}
        ).explain()

        # Navigate the explain output to find the winning plan
        winning_plan = explain_result.get("queryPlanner", {}).get("winningPlan", {})

        # Pretty print the winning plan
        print("  Winning Plan:")
        plan_str = json.dumps(winning_plan, indent=4, default=str)
        for line in plan_str.split("\n"):
            print(f"    {line}")

        # Extract the scan type
        def find_stage(plan, target="IXSCAN"):
            """Recursively find a stage type in the query plan."""
            stage = plan.get("stage", "")
            if target in stage:
                return plan
            for child in [plan.get("inputStage"), plan.get("child")]:
                if child:
                    result = find_stage(child, target)
                    if result:
                        return result
            return None

        ix_scan = find_stage(winning_plan, "IXSCAN")
        coll_scan = find_stage(winning_plan, "COLLSCAN")

        print()
        if ix_scan:
            print("  [OK] IXSCAN (Index Scan) detected!")
            print(f"  Index used: {ix_scan.get('indexName', 'unknown')}")
            print("  This confirms the index on roll_no is being used.")
        elif coll_scan:
            print("  [WARNING] COLLSCAN (Collection Scan) detected - no index used!")
        else:
            print(f"  Plan stage: {winning_plan.get('stage', 'unknown')}")

        # Also show explain for a non-indexed field for comparison
        print("\n\n--- explain() on NON-indexed query: find by name (no index) ---")
        print("  Query: db.students.find({ name: 'Aarav Sharma' })")
        print()

        explain_no_idx = db.students.find(
            {"name": "Aarav Sharma"}
        ).explain()

        winning_plan_2 = explain_no_idx.get("queryPlanner", {}).get("winningPlan", {})
        plan_str_2 = json.dumps(winning_plan_2, indent=4, default=str)
        print("  Winning Plan:")
        for line in plan_str_2.split("\n"):
            print(f"    {line}")

        coll_scan_2 = find_stage(winning_plan_2, "COLLSCAN")
        print()
        if coll_scan_2:
            print("  [NOTICE] COLLSCAN detected (as expected - 'name' has no index)")
            print("  This shows the performance difference between indexed and non-indexed queries.")

    run_section(
        "SECTION 8: explain() - Index Usage",
        "08_explain_index.txt",
        demo_explain
    )

    # ============================================================
    # Final Summary
    # ============================================================
    print("\n" + "=" * 70)
    print("  DEMO RUN COMPLETE")
    print("=" * 70)
    print(f"\n  Output files saved to: outputs/")
    for f in sorted(os.listdir("outputs")):
        filepath = os.path.join("outputs", f)
        size = os.path.getsize(filepath)
        print(f"    - {f} ({size:,} bytes)")

    print(f"\n  Final document counts:")
    print(f"    students:  {db.students.count_documents({})}")
    print(f"    questions: {db.questions.count_documents({})}")
    print(f"    attempts:  {db.attempts.count_documents({})}")
    print()


if __name__ == "__main__":
    main()
