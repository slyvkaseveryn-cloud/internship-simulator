import json

from app.handler import handler


def event(method, path, claims=None, body=None):
    ctx = {"http": {"method": method}}
    if claims:
        ctx["authorizer"] = {"jwt": {"claims": claims}}
    return {"rawPath": path, "requestContext": ctx, "body": json.dumps(body) if body is not None else None}


def call(*a, **k):
    r = handler(event(*a, **k), None)
    return r["statusCode"], json.loads(r["body"])


def test_health_is_public():
    assert call("GET", "/api/public/health") == (200, {"ok": True})


def test_me_needs_a_user():
    assert call("GET", "/api/me")[0] == 401


def test_me_reads_groups_from_claims():
    status, body = call("GET", "/api/me", claims={"sub": "u1", "email": "a@b.c", "cognito:groups": "[reviewers]"})
    assert status == 200 and body == {"email": "a@b.c", "isReviewer": True}


def test_unknown_route_is_404():
    assert call("GET", "/api/nope", claims={"sub": "u1"})[0] == 404
