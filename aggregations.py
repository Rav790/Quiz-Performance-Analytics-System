"""
aggregations.py - Aggregation Pipelines for Quiz Analytics
============================================================
Eight aggregation pipelines that produce meaningful analytics:
  1. Topic-wise accuracy (whole class)
  2. Leaderboard (top 10 students)
  3. Average time per question by difficulty
  4. Monthly attempts trend
  5. Weakest topic per student
  6. Hardest questions
  7. Score distribution (buckets)
  8. Single-student dashboard ($facet)

Plus bonus pipelines:
  - Pass/Fail labeling with $addFields + $cond
  - $setWindowFields for ranking (if server supports it)

Each pipeline is clearly commented stage by stage.
Results are printed as tables using the tabulate library.
"""

from bson import ObjectId
from tabulate import tabulate
from config import get_database


# ============================================================
# Pipeline 1: Topic-wise Accuracy (Whole Class)
# ============================================================

def topic_wise_accuracy(db):
    """
    Calculate overall accuracy per topic across all students.
    Shows which topics students struggle with the most.

    Pipeline stages:
      1. $unwind: Flatten the answers array so each answer is a separate document
      2. $group: Group by topic, count total answers and correct answers
      3. $project: Calculate accuracy_percent using $divide, $multiply, $round
      4. $sort: Sort ascending so weakest topics appear first

    mongosh equivalent:
        db.attempts.aggregate([
            { $unwind: "$answers" },
            { $group: {
                _id: "$answers.topic",
                total_answers: { $sum: 1 },
                correct_answers: { $sum: { $cond: ["$answers.is_correct", 1, 0] } }
            }},
            { $project: {
                topic: "$_id", _id: 0,
                total_answers: 1,
                correct_answers: 1,
                accuracy_percent: {
                    $round: [{ $multiply: [{ $divide: ["$correct_answers", "$total_answers"] }, 100] }, 2]
                }
            }},
            { $sort: { accuracy_percent: 1 } }
        ])
    """
    pipeline = [
        # Stage 1: Flatten answers array
        {"$unwind": "$answers"},

        # Stage 2: Group by topic and count totals
        {"$group": {
            "_id": "$answers.topic",
            "total_answers": {"$sum": 1},
            "correct_answers": {"$sum": {"$cond": ["$answers.is_correct", 1, 0]}}
        }},

        # Stage 3: Calculate percentage
        {"$project": {
            "topic": "$_id",
            "_id": 0,
            "total_answers": 1,
            "correct_answers": 1,
            "accuracy_percent": {
                "$round": [
                    {"$multiply": [
                        {"$divide": ["$correct_answers", "$total_answers"]},
                        100
                    ]},
                    2
                ]
            }
        }},

        # Stage 4: Weakest topics first
        {"$sort": {"accuracy_percent": 1}}
    ]

    results = list(db.attempts.aggregate(pipeline))
    print("\n=== Topic-wise Accuracy (Whole Class) ===")
    headers = ["Topic", "Total Answers", "Correct", "Accuracy %"]
    rows = [[r["topic"], r["total_answers"], r["correct_answers"], r["accuracy_percent"]] for r in results]
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return results


# ============================================================
# Pipeline 2: Leaderboard (Top 10 Students)
# ============================================================

def leaderboard(db):
    """
    Top 10 students by average score, with at least 3 attempts.
    Uses $lookup to join student names.

    Pipeline stages:
      1. $group: Group by student_id, calculate average score and attempt count
      2. $match: Filter to students with >= 3 attempts (meaningful average)
      3. $sort: Descending by average score
      4. $limit: Top 10 only
      5. $lookup: Join with students collection to get name and roll_no
      6. $unwind: Flatten the lookup result (1-to-1 relationship)
      7. $project: Clean output with only needed fields

    mongosh equivalent:
        db.attempts.aggregate([
            { $group: {
                _id: "$student_id",
                avg_score: { $avg: "$score_percent" },
                attempt_count: { $sum: 1 }
            }},
            { $match: { attempt_count: { $gte: 3 } } },
            { $sort: { avg_score: -1 } },
            { $limit: 10 },
            { $lookup: {
                from: "students",
                localField: "_id",
                foreignField: "_id",
                as: "student"
            }},
            { $unwind: "$student" },
            { $project: {
                _id: 0,
                name: "$student.name",
                roll_no: "$student.roll_no",
                avg_score: { $round: ["$avg_score", 2] },
                attempt_count: 1
            }}
        ])
    """
    pipeline = [
        {"$group": {
            "_id": "$student_id",
            "avg_score": {"$avg": "$score_percent"},
            "attempt_count": {"$sum": 1}
        }},
        {"$match": {"attempt_count": {"$gte": 3}}},
        {"$sort": {"avg_score": -1}},
        {"$limit": 10},
        {"$lookup": {
            "from": "students",
            "localField": "_id",
            "foreignField": "_id",
            "as": "student"
        }},
        {"$unwind": "$student"},
        {"$project": {
            "_id": 0,
            "name": "$student.name",
            "roll_no": "$student.roll_no",
            "avg_score": {"$round": ["$avg_score", 2]},
            "attempt_count": 1
        }}
    ]

    results = list(db.attempts.aggregate(pipeline))
    print("\n=== Leaderboard (Top 10 Students) ===")
    headers = ["Rank", "Name", "Roll No", "Avg Score %", "Attempts"]
    rows = [[i+1, r["name"], r["roll_no"], r["avg_score"], r["attempt_count"]]
            for i, r in enumerate(results)]
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return results


# ============================================================
# Pipeline 3: Average Time per Question by Difficulty
# ============================================================

def avg_time_by_difficulty(db):
    """
    Average time spent and accuracy per question difficulty level.
    Helps identify if hard questions are taking too long.

    Pipeline stages:
      1. $unwind: Flatten answers
      2. $group: Group by difficulty, get avg time and accuracy

    mongosh equivalent:
        db.attempts.aggregate([
            { $unwind: "$answers" },
            { $group: {
                _id: "$answers.difficulty",
                avg_time_sec: { $avg: "$answers.time_spent_sec" },
                total: { $sum: 1 },
                correct: { $sum: { $cond: ["$answers.is_correct", 1, 0] } }
            }},
            { $project: {
                difficulty: "$_id", _id: 0,
                avg_time_sec: { $round: ["$avg_time_sec", 1] },
                accuracy_percent: {
                    $round: [{ $multiply: [{ $divide: ["$correct", "$total"] }, 100] }, 2]
                }
            }},
            { $sort: { avg_time_sec: 1 } }
        ])
    """
    pipeline = [
        {"$unwind": "$answers"},
        {"$group": {
            "_id": "$answers.difficulty",
            "avg_time_sec": {"$avg": "$answers.time_spent_sec"},
            "total": {"$sum": 1},
            "correct": {"$sum": {"$cond": ["$answers.is_correct", 1, 0]}}
        }},
        {"$project": {
            "difficulty": "$_id", "_id": 0,
            "avg_time_sec": {"$round": ["$avg_time_sec", 1]},
            "accuracy_percent": {
                "$round": [{"$multiply": [{"$divide": ["$correct", "$total"]}, 100]}, 2]
            }
        }},
        {"$sort": {"avg_time_sec": 1}}
    ]

    results = list(db.attempts.aggregate(pipeline))
    print("\n=== Average Time per Question by Difficulty ===")
    headers = ["Difficulty", "Avg Time (sec)", "Accuracy %"]
    rows = [[r["difficulty"], r["avg_time_sec"], r["accuracy_percent"]] for r in results]
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return results


# ============================================================
# Pipeline 4: Monthly Attempts Trend
# ============================================================

def monthly_trend(db):
    """
    Number of attempts and average score per month.
    Useful for tracking engagement and performance over time.

    Pipeline stages:
      1. $group: Group by month string (YYYY-MM) using $dateToString
      2. $sort: Chronological order

    mongosh equivalent:
        db.attempts.aggregate([
            { $group: {
                _id: { $dateToString: { format: "%Y-%m", date: "$attempted_at" } },
                attempt_count: { $sum: 1 },
                avg_score: { $avg: "$score_percent" }
            }},
            { $project: {
                month: "$_id", _id: 0,
                attempt_count: 1,
                avg_score: { $round: ["$avg_score", 2] }
            }},
            { $sort: { month: 1 } }
        ])
    """
    pipeline = [
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$attempted_at"}},
            "attempt_count": {"$sum": 1},
            "avg_score": {"$avg": "$score_percent"}
        }},
        {"$project": {
            "month": "$_id", "_id": 0,
            "attempt_count": 1,
            "avg_score": {"$round": ["$avg_score", 2]}
        }},
        {"$sort": {"month": 1}}
    ]

    results = list(db.attempts.aggregate(pipeline))
    print("\n=== Monthly Attempts Trend ===")
    headers = ["Month", "Attempts", "Avg Score %"]
    rows = [[r["month"], r["attempt_count"], r["avg_score"]] for r in results]
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return results


# ============================================================
# Pipeline 5: Weakest Topic per Student
# ============================================================

def weakest_topic_per_student(db):
    """
    Find each student's weakest topic (lowest accuracy).
    Teachers can use this to recommend targeted practice.

    Pipeline stages:
      1. $unwind: Flatten answers
      2. First $group: Group by (student_id, topic) to get per-student-per-topic accuracy
      3. $sort: Sort by accuracy ascending so $first picks the worst
      4. Second $group: Group by student_id, use $first to pick weakest topic
      5. $lookup: Join student names
      6. $unwind: Flatten lookup
      7. $project: Clean output

    mongosh equivalent:
        db.attempts.aggregate([
            { $unwind: "$answers" },
            { $group: {
                _id: { student_id: "$student_id", topic: "$answers.topic" },
                total: { $sum: 1 },
                correct: { $sum: { $cond: ["$answers.is_correct", 1, 0] } }
            }},
            { $project: {
                accuracy: { $round: [{ $multiply: [{ $divide: ["$correct", "$total"] }, 100] }, 2] }
            }},
            { $sort: { accuracy: 1 } },
            { $group: {
                _id: "$_id.student_id",
                weakest_topic: { $first: "$_id.topic" },
                weakest_accuracy: { $first: "$accuracy" }
            }},
            { $lookup: { from: "students", localField: "_id", foreignField: "_id", as: "student" } },
            { $unwind: "$student" },
            { $project: {
                _id: 0,
                name: "$student.name",
                roll_no: "$student.roll_no",
                weakest_topic: 1,
                weakest_accuracy: 1
            }},
            { $sort: { weakest_accuracy: 1 } }
        ])
    """
    pipeline = [
        {"$unwind": "$answers"},
        # Group by student + topic
        {"$group": {
            "_id": {"student_id": "$student_id", "topic": "$answers.topic"},
            "total": {"$sum": 1},
            "correct": {"$sum": {"$cond": ["$answers.is_correct", 1, 0]}}
        }},
        # Calculate accuracy
        {"$project": {
            "accuracy": {"$round": [{"$multiply": [{"$divide": ["$correct", "$total"]}, 100]}, 2]}
        }},
        # Sort by worst accuracy first
        {"$sort": {"accuracy": 1}},
        # Pick the weakest topic per student using $first
        {"$group": {
            "_id": "$_id.student_id",
            "weakest_topic": {"$first": "$_id.topic"},
            "weakest_accuracy": {"$first": "$accuracy"}
        }},
        # Join student names
        {"$lookup": {
            "from": "students", "localField": "_id",
            "foreignField": "_id", "as": "student"
        }},
        {"$unwind": "$student"},
        {"$project": {
            "_id": 0,
            "name": "$student.name",
            "roll_no": "$student.roll_no",
            "weakest_topic": 1,
            "weakest_accuracy": 1
        }},
        {"$sort": {"weakest_accuracy": 1}}
    ]

    results = list(db.attempts.aggregate(pipeline))
    print("\n=== Weakest Topic per Student ===")
    headers = ["Name", "Roll No", "Weakest Topic", "Accuracy %"]
    rows = [[r["name"], r["roll_no"], r["weakest_topic"], r["weakest_accuracy"]]
            for r in results[:15]]  # Show top 15 weakest
    if len(results) > 15:
        rows.append(["...", "...", "...", "..."])
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return results


# ============================================================
# Pipeline 6: Hardest Questions
# ============================================================

def hardest_questions(db):
    """
    Find the 5 hardest questions (lowest correct rate), with minimum 5 attempts.
    Helps teachers identify questions that may need revision or extra teaching.

    Pipeline stages:
      1. $unwind: Flatten answers
      2. $group: Group by question_id, count attempts and correct rate
      3. $match: Only questions attempted at least 5 times
      4. $sort: Ascending by correct_rate (hardest first)
      5. $limit: Top 5 hardest
      6. $lookup: Join with questions to get the question text
      7. $unwind: Flatten lookup
      8. $project: Clean output

    mongosh equivalent:
        db.attempts.aggregate([
            { $unwind: "$answers" },
            { $group: {
                _id: "$answers.question_id",
                attempts: { $sum: 1 },
                correct: { $sum: { $cond: ["$answers.is_correct", 1, 0] } }
            }},
            { $project: {
                attempts: 1,
                correct_rate: { $round: [{ $multiply: [{ $divide: ["$correct", "$attempts"] }, 100] }, 2] }
            }},
            { $match: { attempts: { $gte: 5 } } },
            { $sort: { correct_rate: 1 } },
            { $limit: 5 },
            { $lookup: { from: "questions", localField: "_id", foreignField: "_id", as: "question" } },
            { $unwind: "$question" },
            { $project: {
                _id: 0,
                question_text: "$question.text",
                topic: "$question.topic",
                difficulty: "$question.difficulty",
                attempts: 1,
                correct_rate: 1
            }}
        ])
    """
    pipeline = [
        {"$unwind": "$answers"},
        {"$group": {
            "_id": "$answers.question_id",
            "attempts": {"$sum": 1},
            "correct": {"$sum": {"$cond": ["$answers.is_correct", 1, 0]}}
        }},
        {"$project": {
            "attempts": 1,
            "correct_rate": {"$round": [{"$multiply": [{"$divide": ["$correct", "$attempts"]}, 100]}, 2]}
        }},
        {"$match": {"attempts": {"$gte": 5}}},
        {"$sort": {"correct_rate": 1}},
        {"$limit": 5},
        {"$lookup": {
            "from": "questions", "localField": "_id",
            "foreignField": "_id", "as": "question"
        }},
        {"$unwind": "$question"},
        {"$project": {
            "_id": 0,
            "question_text": "$question.text",
            "topic": "$question.topic",
            "difficulty": "$question.difficulty",
            "attempts": 1,
            "correct_rate": 1
        }}
    ]

    results = list(db.attempts.aggregate(pipeline))
    print("\n=== Hardest Questions (Top 5) ===")
    headers = ["Question", "Topic", "Difficulty", "Attempts", "Correct Rate %"]
    rows = [[r["question_text"][:50] + "...", r["topic"], r["difficulty"],
             r["attempts"], r["correct_rate"]] for r in results]
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return results


# ============================================================
# Pipeline 7: Score Distribution (Buckets)
# ============================================================

def score_distribution(db):
    """
    Categorize attempts into score buckets: Poor, Average, Good, Excellent.
    Shows the overall distribution of quiz performance.

    Pipeline stages:
      1. $bucket: Group score_percent into ranges with counts

    Note: $bucket boundaries are exclusive of the upper bound,
    so [0,40) = Poor, [40,60) = Average, [60,80) = Good, [80,101) = Excellent.
    We use 101 instead of 100 because the upper boundary is exclusive.

    mongosh equivalent:
        db.attempts.aggregate([
            { $bucket: {
                groupBy: "$score_percent",
                boundaries: [0, 40, 60, 80, 101],
                default: "Other",
                output: {
                    count: { $sum: 1 },
                    avg_score: { $avg: "$score_percent" }
                }
            }}
        ])
    """
    pipeline = [
        {"$bucket": {
            "groupBy": "$score_percent",
            "boundaries": [0, 40, 60, 80, 101],
            "default": "Other",
            "output": {
                "count": {"$sum": 1},
                "avg_score": {"$avg": "$score_percent"}
            }
        }}
    ]

    results = list(db.attempts.aggregate(pipeline))

    # Map bucket boundaries to labels
    labels = {0: "Poor (0-39%)", 40: "Average (40-59%)", 60: "Good (60-79%)", 80: "Excellent (80-100%)"}

    print("\n=== Score Distribution ===")
    headers = ["Category", "Count", "Avg Score %"]
    rows = []
    for r in results:
        label = labels.get(r["_id"], f"Other ({r['_id']})")
        rows.append([label, r["count"], round(r["avg_score"], 2)])
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return results


# ============================================================
# Pipeline 8: Single-Student Dashboard ($facet)
# ============================================================

def student_dashboard(db, roll_no):
    """
    Comprehensive dashboard for a single student using $facet.
    Returns in ONE aggregation call:
      (a) Overall stats (total attempts, avg score, total time)
      (b) Topic-wise accuracy breakdown
      (c) Last 5 attempts

    $facet runs multiple pipelines in parallel on the same input,
    so the database only scans the data once.

    mongosh equivalent:
        var student = db.students.findOne({ roll_no: "LPU2026001" })
        db.attempts.aggregate([
            { $match: { student_id: student._id } },
            { $facet: {
                overall_stats: [
                    { $group: {
                        _id: null,
                        total_attempts: { $sum: 1 },
                        avg_score: { $avg: "$score_percent" },
                        total_time_min: { $sum: "$time_taken_sec" },
                        best_score: { $max: "$score_percent" },
                        worst_score: { $min: "$score_percent" }
                    }}
                ],
                topic_accuracy: [
                    { $unwind: "$answers" },
                    { $group: {
                        _id: "$answers.topic",
                        total: { $sum: 1 },
                        correct: { $sum: { $cond: ["$answers.is_correct", 1, 0] } }
                    }},
                    { $project: {
                        topic: "$_id", _id: 0,
                        accuracy: { $round: [{ $multiply: [{ $divide: ["$correct", "$total"] }, 100] }, 2] }
                    }},
                    { $sort: { accuracy: -1 } }
                ],
                recent_attempts: [
                    { $sort: { attempted_at: -1 } },
                    { $limit: 5 },
                    { $project: {
                        quiz_title: 1, score_percent: 1,
                        attempted_at: 1, correct_count: 1,
                        total_questions: 1, _id: 0
                    }}
                ]
            }}
        ])
    """
    # First, find the student by roll number
    student = db.students.find_one({"roll_no": roll_no})
    if not student:
        print(f"\n  [ERROR] No student found with roll_no: {roll_no}")
        return None

    pipeline = [
        # Filter to this student's attempts only
        {"$match": {"student_id": student["_id"]}},

        # $facet: run 3 sub-pipelines in parallel
        {"$facet": {
            "overall_stats": [
                {"$group": {
                    "_id": None,
                    "total_attempts": {"$sum": 1},
                    "avg_score": {"$avg": "$score_percent"},
                    "total_time_sec": {"$sum": "$time_taken_sec"},
                    "best_score": {"$max": "$score_percent"},
                    "worst_score": {"$min": "$score_percent"}
                }}
            ],
            "topic_accuracy": [
                {"$unwind": "$answers"},
                {"$group": {
                    "_id": "$answers.topic",
                    "total": {"$sum": 1},
                    "correct": {"$sum": {"$cond": ["$answers.is_correct", 1, 0]}}
                }},
                {"$project": {
                    "topic": "$_id", "_id": 0,
                    "accuracy": {"$round": [
                        {"$multiply": [{"$divide": ["$correct", "$total"]}, 100]}, 2
                    ]}
                }},
                {"$sort": {"accuracy": -1}}
            ],
            "recent_attempts": [
                {"$sort": {"attempted_at": -1}},
                {"$limit": 5},
                {"$project": {
                    "quiz_title": 1, "score_percent": 1,
                    "attempted_at": 1, "correct_count": 1,
                    "total_questions": 1, "_id": 0
                }}
            ]
        }}
    ]

    results = list(db.attempts.aggregate(pipeline))
    data = results[0] if results else {}

    # Print the dashboard
    print(f"\n{'='*60}")
    print(f"  STUDENT DASHBOARD: {student['name']} ({roll_no})")
    print(f"  Branch: {student['branch']} | Semester: {student['semester']}")
    print(f"{'='*60}")

    # Overall stats
    if data.get("overall_stats"):
        stats = data["overall_stats"][0]
        print(f"\n  [Stats] Overall Statistics:")
        print(f"     Total Attempts:  {stats['total_attempts']}")
        print(f"     Average Score:   {round(stats['avg_score'], 2)}%")
        print(f"     Best Score:      {stats['best_score']}%")
        print(f"     Worst Score:     {stats['worst_score']}%")
        print(f"     Total Time:      {stats['total_time_sec'] // 60} minutes")

    # Topic accuracy
    if data.get("topic_accuracy"):
        print(f"\n  [Topic] Topic-wise Accuracy:")
        headers = ["Topic", "Accuracy %"]
        rows = [[t["topic"], t["accuracy"]] for t in data["topic_accuracy"]]
        print(tabulate(rows, headers=headers, tablefmt="grid", stralign="left"))

    # Recent attempts
    if data.get("recent_attempts"):
        print(f"\n  [Recent] Last 5 Attempts:")
        headers = ["Quiz", "Score %", "Correct", "Date"]
        rows = [[
            a["quiz_title"],
            a["score_percent"],
            f"{a['correct_count']}/{a['total_questions']}",
            a["attempted_at"].strftime("%Y-%m-%d %H:%M")
        ] for a in data["recent_attempts"]]
        print(tabulate(rows, headers=headers, tablefmt="grid"))

    return data


# ============================================================
# Bonus: Pass/Fail Labeling with $addFields + $cond
# ============================================================

def pass_fail_labeling(db):
    """
    Label each attempt as 'Pass' or 'Fail' using $addFields and $cond.
    Passing threshold is 40%.

    This demonstrates $addFields (adds new computed fields to documents)
    and $cond (conditional expression, like an if-else).

    mongosh equivalent:
        db.attempts.aggregate([
            { $addFields: {
                result_label: {
                    $cond: {
                        if: { $gte: ["$score_percent", 40] },
                        then: "Pass",
                        else: "Fail"
                    }
                }
            }},
            { $group: {
                _id: "$result_label",
                count: { $sum: 1 },
                avg_score: { $avg: "$score_percent" }
            }},
            { $sort: { _id: 1 } }
        ])
    """
    pipeline = [
        # Add a 'result_label' field: "Pass" if score >= 40, else "Fail"
        {"$addFields": {
            "result_label": {
                "$cond": {
                    "if": {"$gte": ["$score_percent", 40]},
                    "then": "Pass",
                    "else": "Fail"
                }
            }
        }},
        # Group by the label to get counts
        {"$group": {
            "_id": "$result_label",
            "count": {"$sum": 1},
            "avg_score": {"$avg": "$score_percent"}
        }},
        {"$sort": {"_id": 1}}
    ]

    results = list(db.attempts.aggregate(pipeline))
    print("\n=== Pass/Fail Distribution ($addFields + $cond) ===")
    headers = ["Result", "Count", "Avg Score %"]
    rows = [[r["_id"], r["count"], round(r["avg_score"], 2)] for r in results]
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    return results


# ============================================================
# Bonus: Rank Students with $setWindowFields (MongoDB 5.0+)
# ============================================================

def rank_students(db):
    """
    Rank students by average score using $setWindowFields (requires MongoDB 5.0+).
    Falls back gracefully if the server doesn't support it.

    mongosh equivalent:
        db.attempts.aggregate([
            { $group: {
                _id: "$student_id",
                avg_score: { $avg: "$score_percent" },
                attempts: { $sum: 1 }
            }},
            { $setWindowFields: {
                sortBy: { avg_score: -1 },
                output: {
                    rank: { $rank: {} }
                }
            }},
            { $lookup: { from: "students", localField: "_id", foreignField: "_id", as: "student" } },
            { $unwind: "$student" },
            { $project: {
                _id: 0, rank: 1,
                name: "$student.name",
                roll_no: "$student.roll_no",
                avg_score: { $round: ["$avg_score", 2] }
            }},
            { $limit: 10 }
        ])
    """
    pipeline = [
        {"$group": {
            "_id": "$student_id",
            "avg_score": {"$avg": "$score_percent"},
            "attempts": {"$sum": 1}
        }},
        {"$setWindowFields": {
            "sortBy": {"avg_score": -1},
            "output": {
                "rank": {"$rank": {}}
            }
        }},
        {"$lookup": {
            "from": "students", "localField": "_id",
            "foreignField": "_id", "as": "student"
        }},
        {"$unwind": "$student"},
        {"$project": {
            "_id": 0, "rank": 1,
            "name": "$student.name",
            "roll_no": "$student.roll_no",
            "avg_score": {"$round": ["$avg_score", 2]}
        }},
        {"$limit": 10}
    ]

    try:
        results = list(db.attempts.aggregate(pipeline))
        print("\n=== Student Rankings ($setWindowFields + $rank) ===")
        headers = ["Rank", "Name", "Roll No", "Avg Score %"]
        rows = [[r["rank"], r["name"], r["roll_no"], r["avg_score"]] for r in results]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        return results
    except Exception as e:
        print(f"\n[NOTE] $setWindowFields not supported on this server version: {e}")
        print("  This feature requires MongoDB 5.0 or later.")
        return []


# ============================================================
# Run All Aggregations
# ============================================================

def run_all_aggregations(db, student_roll_no="LPU2026001"):
    """Run all 8 main aggregation pipelines plus bonus pipelines."""
    print("\n" + "=" * 60)
    print("  RUNNING ALL AGGREGATION PIPELINES")
    print("=" * 60)

    results = {}
    results["topic_accuracy"] = topic_wise_accuracy(db)
    results["leaderboard"] = leaderboard(db)
    results["time_by_difficulty"] = avg_time_by_difficulty(db)
    results["monthly_trend"] = monthly_trend(db)
    results["weakest_topics"] = weakest_topic_per_student(db)
    results["hardest_questions"] = hardest_questions(db)
    results["score_distribution"] = score_distribution(db)
    results["student_dashboard"] = student_dashboard(db, student_roll_no)

    # Bonus pipelines
    results["pass_fail"] = pass_fail_labeling(db)
    results["rankings"] = rank_students(db)

    return results


if __name__ == "__main__":
    db = get_database()
    run_all_aggregations(db, "LPU2026001")
