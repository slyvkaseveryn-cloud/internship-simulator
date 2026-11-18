from helpers import REVIEWER, STUDENT, call, events


def test_health_is_public():
    assert call("GET", "/api/public/health") == (200, {"ok": True})


def test_me_needs_a_user():
    assert call("GET", "/api/me")[0] == 401


def test_unknown_route_is_404():
    assert call("GET", "/api/nope", claims=STUDENT)[0] == 404


def test_first_me_creates_profile_and_logs_signup_once(dynamo):
    status, body = call("GET", "/api/me", claims=STUDENT, anon="anon-1")
    assert status == 200
    assert body == {"email": "olya@example.org", "name": "", "profession": None, "isReviewer": False}
    call("GET", "/api/me", claims=STUDENT)
    signups = events(dynamo, "signed_up")
    assert len(signups) == 1 and signups[0]["anon"] == "anon-1"


def test_reviewer_flag_comes_from_groups():
    assert call("GET", "/api/me", claims=REVIEWER)[1]["isReviewer"] is True


def test_choose_live_profession(dynamo):
    assert call("PUT", "/api/me/profession", claims=STUDENT, body={"profession": "qa"}) == (200, {"profession": "qa"})
    assert call("GET", "/api/me", claims=STUDENT)[1]["profession"] == "qa"
    assert [e["value"] for e in events(dynamo, "profession_chosen")] == ["qa"]


def test_soon_or_unknown_profession_is_rejected():
    assert call("PUT", "/api/me/profession", claims=STUDENT, body={"profession": "hr"})[0] == 400
    assert call("PUT", "/api/me/profession", claims=STUDENT, body={"profession": "x"})[0] == 400


def test_client_event_whitelist(dynamo):
    assert call("POST", "/api/events", claims=STUDENT, body={"event": "case_viewed", "caseId": "01-conversion-drop"})[0] == 200
    assert call("POST", "/api/events", claims=STUDENT, body={"event": "case_taken", "caseId": "01-conversion-drop"})[0] == 400
    assert call("POST", "/api/events", claims=STUDENT, body={"event": "case_viewed", "caseId": "nope"})[0] == 404
    assert len(events(dynamo, "case_viewed")) == 1


def test_bad_json_is_400():
    from app.handler import handler
    r = handler({"rawPath": "/api/me", "requestContext": {"http": {"method": "GET"}}, "body": "{"}, None)
    assert r["statusCode"] == 400
