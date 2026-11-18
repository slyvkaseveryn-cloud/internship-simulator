"""HTTP API entry point (API Gateway HTTP API, payload format 2.0).

API Gateway checks the Cognito JWT on every route under /api/ except /api/public/*.
The verified claims arrive in requestContext.authorizer.jwt.claims.
"""
import json
import logging

from . import routes

log = logging.getLogger()
log.setLevel(logging.INFO)


def response(status: int, body) -> dict:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json; charset=utf-8", "cache-control": "no-store"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def current_user(event: dict) -> dict | None:
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims")
    if not claims:
        return None
    groups = claims.get("cognito:groups") or ""
    # API Gateway passes list claims as "[a b]"
    groups = groups.strip("[]").replace(",", " ").split() if isinstance(groups, str) else list(groups)
    return {"sub": claims["sub"], "email": claims.get("email", ""), "name": claims.get("name", ""), "groups": groups}


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "/")
    body = None
    if event.get("body"):
        try:
            body = json.loads(event["body"])
        except ValueError:
            return response(400, {"error": "invalid_json"})
    try:
        anon = (event.get("headers") or {}).get("x-anon-id", "")[:64] or None
        status, payload = routes.dispatch(method, path, body, current_user(event), anon)
    except routes.HttpError as e:
        status, payload = e.status, {"error": e.code}
    except Exception:
        log.exception("unhandled error on %s %s", method, path)
        status, payload = 500, {"error": "internal"}
    return response(status, payload)
