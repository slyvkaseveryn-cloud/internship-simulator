from helpers import STUDENT, call, events

GOOD = {"liked": "Дані як справжні", "hindered": "Довго качався CSV", "realism": 4, "wouldPay": "maybe",
        "caseId": "01-conversion-drop"}


def test_feedback_is_stored_with_email_and_time(dynamo):
    assert call("POST", "/api/feedback", claims=STUDENT, body=GOOD) == (201, {"ok": True})
    items = dynamo.query(KeyConditionExpression="pk = :p", ExpressionAttributeValues={":p": "FEEDBACK"})["Items"]
    assert len(items) == 1
    fb = items[0]
    assert fb["email"] == "olya@example.org" and fb["ts"] and fb["realism"] == 4 and fb["would_pay"] == "maybe"
    assert fb["liked"] == "Дані як справжні" and fb["case_id"] == "01-conversion-drop"
    assert [e["value"] for e in events(dynamo, "feedback_sent")] == ["4"]


def test_texts_are_optional():
    assert call("POST", "/api/feedback", claims=STUDENT, body={"realism": 5, "wouldPay": "yes"})[0] == 201


def test_feedback_validation():
    for bad in ({"realism": 0}, {"realism": 6}, {"realism": "4"}, {"realism": True}, {"wouldPay": "sure"},
                {"liked": "x" * 2001}, {"caseId": "nope"}):
        assert call("POST", "/api/feedback", claims=STUDENT, body={**GOOD, **bad})[0] in (400, 404), bad


def test_feedback_needs_sign_in():
    assert call("POST", "/api/feedback", body=GOOD)[0] == 401
