from helpers import STUDENT, call, events

CASE = "05-qa-checkout"
OTHER = {"sub": "u-other", "email": "other@example.org", "cognito:groups": ""}
WORK = {"link": "https://docs.google.com/spreadsheets/d/abc", "conclusion": "Реліз не можна: два критичні баги."}


def test_take_case_sets_deadline_and_is_idempotent(dynamo):
    status, a = call("POST", f"/api/cases/{CASE}/take", claims=STUDENT)
    assert status == 201 and a["status"] == "taken" and a["deadline"] > a["takenAt"]
    assert call("POST", f"/api/cases/{CASE}/take", claims=STUDENT)[0] == 200
    assert len(events(dynamo, "case_taken")) == 1


def test_unknown_case_is_404():
    assert call("POST", "/api/cases/99-nope/take", claims=STUDENT)[0] == 404


def test_cannot_submit_without_taking():
    assert call("POST", f"/api/cases/{CASE}/submit", claims=STUDENT, body=WORK) == (409, {"error": "case_not_taken"})


def test_submit_and_resubmit(dynamo):
    call("POST", f"/api/cases/{CASE}/take", claims=STUDENT)
    status, a = call("POST", f"/api/cases/{CASE}/submit", claims=STUDENT, body=WORK)
    assert status == 200 and a["status"] == "submitted" and a["submission"]["link"] == WORK["link"]
    call("POST", f"/api/cases/{CASE}/submit", claims=STUDENT, body={**WORK, "conclusion": "Оновлений висновок"})
    assert call("GET", f"/api/cases/{CASE}/attempt", claims=STUDENT)[1]["attempt"]["submission"]["conclusion"] == "Оновлений висновок"
    assert [e.get("value") for e in events(dynamo, "submitted")] == [None, "resubmitted"]


def test_submission_validation():
    call("POST", f"/api/cases/{CASE}/take", claims=STUDENT)
    assert call("POST", f"/api/cases/{CASE}/submit", claims=STUDENT, body={**WORK, "link": "javascript:alert(1)"})[0] == 400
    assert call("POST", f"/api/cases/{CASE}/submit", claims=STUDENT, body={**WORK, "conclusion": "  "})[0] == 400
    assert call("POST", f"/api/cases/{CASE}/submit", claims=STUDENT, body={**WORK, "conclusion": "x" * 2001})[0] == 400


def test_attempts_are_private_to_their_owner():
    call("POST", f"/api/cases/{CASE}/take", claims=STUDENT)
    assert call("GET", "/api/attempts", claims=OTHER)[1] == {"attempts": []}
    assert call("POST", f"/api/cases/{CASE}/submit", claims=OTHER, body=WORK)[0] == 409
    assert len(call("GET", "/api/attempts", claims=STUDENT)[1]["attempts"]) == 1
