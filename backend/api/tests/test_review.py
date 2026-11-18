from helpers import REVIEWER, STUDENT, call, events

CASE = "01-conversion-drop"
REVIEW = {"good": "Знайшла дублікати", "fix": "Когорти замість загальної конверсії", "next": "Спробуй SQL"}


def submitted():
    call("POST", f"/api/cases/{CASE}/take", claims=STUDENT)
    call("POST", f"/api/cases/{CASE}/submit", claims=STUDENT, body={"link": "https://colab.research.google.com/x", "conclusion": "Впала через iOS"})


def test_only_reviewers_see_the_queue_and_write_reviews():
    submitted()
    assert call("GET", "/api/review/submissions", claims=STUDENT)[0] == 403
    assert call("POST", f"/api/review/u-student/{CASE}", claims=STUDENT, body=REVIEW)[0] == 403
    assert call("GET", "/api/review/submissions")[0] == 401


def test_queue_lists_submissions_only():
    call("POST", "/api/cases/02-ab-price/take", claims=STUDENT)  # taken, not submitted
    submitted()
    status, body = call("GET", "/api/review/submissions", claims=REVIEWER)
    assert status == 200 and len(body["submissions"]) == 1
    s = body["submissions"][0]
    assert s["email"] == "olya@example.org" and s["userId"] == "u-student" and s["status"] == "submitted"
    assert s["caseTitle"] and s["submission"]["conclusion"] == "Впала через iOS"


def test_review_reaches_the_student_without_reviewer_email(dynamo):
    submitted()
    status, a = call("POST", f"/api/review/u-student/{CASE}", claims=REVIEWER, body=REVIEW)
    assert status == 200 and a["status"] == "reviewed"
    mine = call("GET", f"/api/cases/{CASE}/attempt", claims=STUDENT)[1]["attempt"]
    assert mine["status"] == "reviewed" and mine["review"]["good"] == REVIEW["good"] and "reviewer" not in mine["review"]
    assert [(e["user"], e.get("value")) for e in events(dynamo, "review_sent")] == [("u-student", None)]
    assert call("POST", f"/api/cases/{CASE}/submit", claims=STUDENT, body={"link": "https://x.org", "conclusion": "y"})[0] == 409
    queue = call("GET", "/api/review/submissions", claims=REVIEWER)[1]["submissions"]
    assert queue[0]["status"] == "reviewed"


def test_review_needs_all_three_parts_and_a_submission():
    assert call("POST", f"/api/review/u-student/{CASE}", claims=REVIEWER, body=REVIEW)[0] == 404
    submitted()
    assert call("POST", f"/api/review/u-student/{CASE}", claims=REVIEWER, body={**REVIEW, "fix": ""})[0] == 400
