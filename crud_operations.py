"""
crud_operations.py - Complete CRUD Operations
================================================
All Create, Read, Update, Delete operations for the quiz analytics system.
Each function has a docstring showing the equivalent mongosh command.

Error handling:
  - DuplicateKeyError: caught when inserting a student with existing roll_no/email
  - WriteError: caught when validation rules reject a document
  - General exceptions: caught and printed for robustness
"""

from datetime import datetime, timedelta
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, WriteError
from config import get_database, check_replica_set


# ============================================================
# CREATE Operations
# ============================================================

def add_student(db, roll_no, name, email, branch, semester):
    """
    Insert a single student document.
    Handles DuplicateKeyError (roll_no or email already exists)
    and WriteError (validation fails).

    mongosh equivalent:
        db.students.insertOne({
            roll_no: "LPU2026099",
            name: "Test Student",
            email: "test@lpu.in",
            branch: "CSE",
            semester: 6,
            is_active: true,
            created_at: new Date()
        })
    """
    doc = {
        "roll_no": roll_no,
        "name": name,
        "email": email,
        "branch": branch,
        "semester": semester,
        "is_active": True,
        "created_at": datetime.now()
    }
    try:
        result = db.students.insert_one(doc)
        print(f"  [CREATE] Student added: {name} (ID: {result.inserted_id})")
        return result.inserted_id
    except DuplicateKeyError as e:
        print(f"  [ERROR] Duplicate key: {e.details.get('errmsg', str(e))}")
        return None
    except WriteError as e:
        print(f"  [ERROR] Validation failed: {e.details.get('errmsg', str(e))}")
        return None


def add_questions_bulk(db, questions_list):
    """
    Insert multiple questions at once using insert_many.
    ordered=False means it continues inserting even if some fail.

    mongosh equivalent:
        db.questions.insertMany([
            { topic: "DBMS", difficulty: "easy", text: "...", ... },
            { topic: "DSA", difficulty: "medium", text: "...", ... }
        ], { ordered: false })
    """
    try:
        result = db.questions.insert_many(questions_list, ordered=False)
        print(f"  [CREATE] Inserted {len(result.inserted_ids)} questions")
        return result.inserted_ids
    except WriteError as e:
        print(f"  [ERROR] Some questions failed validation: {e}")
        return []


def record_attempt(db, student_id, quiz_title, answers):
    """
    Record a quiz attempt. Computes correct_count, score_percent,
    and time_taken_sec from the answers array for data consistency.

    mongosh equivalent:
        db.attempts.insertOne({
            student_id: ObjectId("..."),
            quiz_title: "DBMS Weekly Quiz 1",
            attempted_at: new Date(),
            time_taken_sec: 320,
            total_questions: 10,
            correct_count: 7,
            score_percent: 70.0,
            answers: [...]
        })
    """
    # Compute derived fields from answers
    correct_count = sum(1 for a in answers if a["is_correct"])
    total_questions = len(answers)
    score_percent = round((correct_count / total_questions) * 100, 2) if total_questions > 0 else 0.0
    time_taken_sec = sum(a["time_spent_sec"] for a in answers)

    doc = {
        "student_id": student_id,
        "quiz_title": quiz_title,
        "attempted_at": datetime.now(),
        "time_taken_sec": time_taken_sec,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "score_percent": float(score_percent),
        "answers": answers
    }
    try:
        result = db.attempts.insert_one(doc)
        print(f"  [CREATE] Attempt recorded: {quiz_title}, Score: {score_percent}% (ID: {result.inserted_id})")
        return result.inserted_id
    except WriteError as e:
        print(f"  [ERROR] Validation failed: {e}")
        return None


# ============================================================
# READ Operations
# ============================================================

def find_student_by_roll(db, roll_no):
    """
    Find a single student by their unique roll number.

    mongosh equivalent:
        db.students.findOne({ roll_no: "LPU2026001" })
    """
    student = db.students.find_one({"roll_no": roll_no})
    if student:
        print(f"  [READ] Found: {student['name']} ({student['roll_no']}) - {student['branch']} Sem {student['semester']}")
    else:
        print(f"  [READ] No student found with roll_no: {roll_no}")
    return student


def list_questions(db, topic=None, difficulty=None, limit=10):
    """
    List questions with optional filters, projection, sort, and limit.
    Uses $and implicitly by combining filters in one dict.

    mongosh equivalent:
        db.questions.find(
            { topic: "DBMS", difficulty: "medium" },
            { text: 1, topic: 1, difficulty: 1, marks: 1 }
        ).sort({ marks: -1 }).limit(10)
    """
    # Build filter dynamically
    query = {}
    if topic:
        query["topic"] = topic
    if difficulty:
        query["difficulty"] = difficulty

    # Projection: only return useful fields (not the full options array)
    projection = {"text": 1, "topic": 1, "difficulty": 1, "marks": 1, "correct_option": 1}

    cursor = db.questions.find(query, projection).sort("marks", -1).limit(limit)
    questions = list(cursor)
    print(f"  [READ] Found {len(questions)} questions (filter: topic={topic}, difficulty={difficulty})")
    for q in questions:
        print(f"    - [{q['difficulty']}] {q['text'][:60]}... ({q['marks']} marks)")
    return questions


def get_student_attempts(db, student_id):
    """
    Get all attempts for a student, sorted newest first.

    mongosh equivalent:
        db.attempts.find(
            { student_id: ObjectId("...") }
        ).sort({ attempted_at: -1 })
    """
    cursor = db.attempts.find(
        {"student_id": student_id}
    ).sort("attempted_at", -1)
    attempts = list(cursor)
    print(f"  [READ] Found {len(attempts)} attempts for student {student_id}")
    for a in attempts[:5]:  # Show only first 5 for brevity
        print(f"    - {a['quiz_title']}: {a['score_percent']}% ({a['attempted_at'].strftime('%Y-%m-%d')})")
    if len(attempts) > 5:
        print(f"    ... and {len(attempts) - 5} more")
    return attempts


def search_students_by_name(db, name_regex):
    """
    Search students by name using case-insensitive regex.
    Demonstrates $regex operator.

    mongosh equivalent:
        db.students.find({ name: { $regex: "sharma", $options: "i" } })
    """
    cursor = db.students.find({
        "name": {"$regex": name_regex, "$options": "i"}
    })
    students = list(cursor)
    print(f"  [READ] Found {len(students)} students matching '{name_regex}':")
    for s in students:
        print(f"    - {s['name']} ({s['roll_no']})")
    return students


def count_documents_examples(db):
    """
    Demonstrate count_documents with various filters.

    mongosh equivalents:
        db.students.countDocuments({})
        db.questions.countDocuments({ topic: "DBMS" })
        db.attempts.countDocuments({ score_percent: { $gte: 70 } })
    """
    total_students = db.students.count_documents({})
    dbms_questions = db.questions.count_documents({"topic": "DBMS"})
    high_scorers = db.attempts.count_documents({"score_percent": {"$gte": 70}})

    print(f"  [COUNT] Total students: {total_students}")
    print(f"  [COUNT] DBMS questions: {dbms_questions}")
    print(f"  [COUNT] Attempts with score >= 70%: {high_scorers}")

    return {
        "total_students": total_students,
        "dbms_questions": dbms_questions,
        "high_score_attempts": high_scorers
    }


def query_with_operators(db):
    """
    Demonstrate MongoDB query operators: $in, $gte/$lte, $and, $or.

    mongosh equivalent:
        // $in: students in CSE or IT
        db.students.find({ branch: { $in: ["CSE", "IT"] } })

        // $gte/$lte: attempts with score between 40 and 80
        db.attempts.find({ score_percent: { $gte: 40, $lte: 80 } })

        // $and: hard DBMS questions
        db.questions.find({ $and: [{ topic: "DBMS" }, { difficulty: "hard" }] })

        // $or: students in semester 7 OR branch CSE
        db.students.find({ $or: [{ semester: 7 }, { branch: "CSE" }] })
    """
    print("\n  --- Query Operator Examples ---")

    # $in: find students in specific branches
    in_result = list(db.students.find(
        {"branch": {"$in": ["CSE", "IT"]}},
        {"name": 1, "branch": 1, "_id": 0}
    ))
    print(f"  [$in] Students in CSE or IT: {len(in_result)}")

    # $gte/$lte: score range
    range_result = db.attempts.count_documents({
        "score_percent": {"$gte": 40, "$lte": 80}
    })
    print(f"  [$gte/$lte] Attempts with score 40-80%: {range_result}")

    # $and: explicit AND (same as combining in one dict, but shown explicitly)
    and_result = list(db.questions.find({
        "$and": [
            {"topic": "DBMS"},
            {"difficulty": "hard"}
        ]
    }))
    print(f"  [$and] Hard DBMS questions: {len(and_result)}")

    # $or: students in sem 7 OR branch CSE
    or_result = list(db.students.find({
        "$or": [
            {"semester": 7},
            {"branch": "CSE"}
        ]
    }, {"name": 1, "branch": 1, "semester": 1, "_id": 0}))
    print(f"  [$or] Sem 7 OR CSE: {len(or_result)}")

    return {
        "in_count": len(in_result),
        "range_count": range_result,
        "and_count": len(and_result),
        "or_count": len(or_result)
    }


# ============================================================
# UPDATE Operations
# ============================================================

def update_student_semester(db, roll_no, new_semester):
    """
    Update a student's semester using $set.

    mongosh equivalent:
        db.students.updateOne(
            { roll_no: "LPU2026001" },
            { $set: { semester: 7 } }
        )
    """
    try:
        result = db.students.update_one(
            {"roll_no": roll_no},
            {"$set": {"semester": new_semester}}
        )
        if result.matched_count:
            print(f"  [UPDATE] {roll_no} semester updated to {new_semester}")
        else:
            print(f"  [UPDATE] No student found with roll_no: {roll_no}")
        return result.modified_count
    except WriteError as e:
        print(f"  [ERROR] Validation failed (semester must be 1-8): {e}")
        return 0


def deactivate_students_of_branch(db, branch):
    """
    Deactivate all students in a branch using update_many with $set.

    mongosh equivalent:
        db.students.updateMany(
            { branch: "ME" },
            { $set: { is_active: false } }
        )
    """
    result = db.students.update_many(
        {"branch": branch},
        {"$set": {"is_active": False}}
    )
    print(f"  [UPDATE] Deactivated {result.modified_count} students in {branch}")
    return result.modified_count


def add_tag_to_question(db, question_id, tag):
    """
    Add a tag to a question using $addToSet (prevents duplicates).

    mongosh equivalent:
        db.questions.updateOne(
            { _id: ObjectId("...") },
            { $addToSet: { tags: "important" } }
        )
    """
    result = db.questions.update_one(
        {"_id": question_id},
        {"$addToSet": {"tags": tag}}
    )
    if result.modified_count:
        print(f"  [UPDATE] Tag '{tag}' added to question {question_id}")
    else:
        print(f"  [UPDATE] Tag '{tag}' already exists or question not found")
    return result.modified_count


def increment_marks_for_hard_questions(db):
    """
    Increase marks by 1 for all hard questions using $inc.

    mongosh equivalent:
        db.questions.updateMany(
            { difficulty: "hard" },
            { $inc: { marks: 1 } }
        )
    """
    result = db.questions.update_many(
        {"difficulty": "hard"},
        {"$inc": {"marks": 1}}
    )
    print(f"  [UPDATE] Incremented marks for {result.modified_count} hard questions")
    return result.modified_count


def upsert_student(db, roll_no, name, email, branch, semester):
    """
    Insert or update a student using upsert=True.
    If the roll_no exists, update the fields; otherwise, insert a new document.

    mongosh equivalent:
        db.students.updateOne(
            { roll_no: "LPU2026099" },
            { $set: { name: "New Student", email: "new@lpu.in", branch: "CSE", semester: 6, is_active: true },
              $setOnInsert: { created_at: new Date() } },
            { upsert: true }
        )
    """
    try:
        result = db.students.update_one(
            {"roll_no": roll_no},
            {
                "$set": {
                    "name": name,
                    "email": email,
                    "branch": branch,
                    "semester": semester,
                    "is_active": True
                },
                # $setOnInsert only applies when a NEW document is created
                "$setOnInsert": {"created_at": datetime.now()}
            },
            upsert=True
        )
        if result.upserted_id:
            print(f"  [UPSERT] New student inserted: {name} (ID: {result.upserted_id})")
        else:
            print(f"  [UPSERT] Existing student updated: {roll_no}")
        return result.upserted_id or result.modified_count
    except (DuplicateKeyError, WriteError) as e:
        print(f"  [ERROR] Upsert failed: {e}")
        return None


def fix_attempt_answer(db, attempt_id, question_id, new_selected_option, new_is_correct):
    """
    Fix a specific answer in an attempt's embedded answers array.
    Uses arrayFilters to target the specific answer by question_id,
    then recomputes score_percent and correct_count for consistency.

    mongosh equivalent:
        db.attempts.updateOne(
            { _id: ObjectId("...") },
            { $set: {
                "answers.$[elem].selected_option": "B",
                "answers.$[elem].is_correct": true
              }
            },
            { arrayFilters: [{ "elem.question_id": ObjectId("...") }] }
        )
    """
    # Step 1: Update the specific answer using arrayFilters
    result = db.attempts.update_one(
        {"_id": attempt_id},
        {"$set": {
            "answers.$[elem].selected_option": new_selected_option,
            "answers.$[elem].is_correct": new_is_correct
        }},
        array_filters=[{"elem.question_id": question_id}]
    )

    if result.modified_count == 0:
        print(f"  [UPDATE] No matching answer found to fix")
        return 0

    # Step 2: Recompute correct_count and score_percent for consistency
    attempt = db.attempts.find_one({"_id": attempt_id})
    if attempt:
        new_correct = sum(1 for a in attempt["answers"] if a["is_correct"])
        new_score = round((new_correct / attempt["total_questions"]) * 100, 2)
        db.attempts.update_one(
            {"_id": attempt_id},
            {"$set": {"correct_count": new_correct, "score_percent": float(new_score)}}
        )
        print(f"  [UPDATE] Answer fixed. New score: {new_score}% ({new_correct}/{attempt['total_questions']} correct)")

    return result.modified_count


# ============================================================
# DELETE Operations
# ============================================================

def delete_question(db, question_id):
    """
    Delete a single question by its _id.

    mongosh equivalent:
        db.questions.deleteOne({ _id: ObjectId("...") })
    """
    result = db.questions.delete_one({"_id": question_id})
    if result.deleted_count:
        print(f"  [DELETE] Question {question_id} deleted")
    else:
        print(f"  [DELETE] Question {question_id} not found")
    return result.deleted_count


def delete_old_attempts(db, before_date):
    """
    Delete all attempts before a certain date using delete_many.

    mongosh equivalent:
        db.attempts.deleteMany({
            attempted_at: { $lt: ISODate("2024-01-01") }
        })
    """
    result = db.attempts.delete_many({
        "attempted_at": {"$lt": before_date}
    })
    print(f"  [DELETE] Deleted {result.deleted_count} attempts before {before_date.strftime('%Y-%m-%d')}")
    return result.deleted_count


def delete_student_with_attempts(db, student_id):
    """
    Delete a student AND all their attempts.
    
    Uses a multi-document transaction if on a replica set (for atomicity).
    Falls back to sequential deletes on standalone deployments.
    
    Why transactions matter:
      Without a transaction on a standalone server, if the student is deleted
      but the attempts delete fails, we'd have orphan attempt documents.
      On a replica set, the transaction ensures both succeed or both fail.

    mongosh equivalent (with transaction):
        session = db.getMongo().startSession()
        session.startTransaction()
        db.attempts.deleteMany({ student_id: ObjectId("...") }, { session })
        db.students.deleteOne({ _id: ObjectId("...") }, { session })
        session.commitTransaction()
    """
    client = db.client
    is_replica = check_replica_set(client)

    if is_replica:
        # Use a transaction for atomic delete (requires replica set)
        with client.start_session() as session:
            with session.start_transaction():
                attempts_result = db.attempts.delete_many(
                    {"student_id": student_id}, session=session
                )
                student_result = db.students.delete_one(
                    {"_id": student_id}, session=session
                )
        print(f"  [DELETE] Transaction: deleted student and {attempts_result.deleted_count} attempts")
        return student_result.deleted_count, attempts_result.deleted_count
    else:
        # Fallback: sequential deletes (no atomicity guarantee on standalone)
        # NOTE: On a standalone MongoDB server, transactions are not supported.
        # If the second delete fails, we could have inconsistent data.
        attempts_result = db.attempts.delete_many({"student_id": student_id})
        student_result = db.students.delete_one({"_id": student_id})
        print(f"  [DELETE] Sequential (no transaction): deleted student and {attempts_result.deleted_count} attempts")
        return student_result.deleted_count, attempts_result.deleted_count


if __name__ == "__main__":
    db = get_database()

    print("\n=== CRUD Operations Demo ===\n")

    # CREATE
    print("--- CREATE ---")
    add_student(db, "LPU2026099", "Demo Student", "demo@lpu.in", "CSE", 6)

    # READ
    print("\n--- READ ---")
    find_student_by_roll(db, "LPU2026001")
    list_questions(db, topic="DBMS", limit=3)
    search_students_by_name(db, "sharma")
    count_documents_examples(db)
    query_with_operators(db)

    # UPDATE
    print("\n--- UPDATE ---")
    update_student_semester(db, "LPU2026099", 7)

    # DELETE
    print("\n--- DELETE ---")
    delete_question(db, db.questions.find_one()["_id"])

    print("\n[DONE] CRUD demo complete!")
