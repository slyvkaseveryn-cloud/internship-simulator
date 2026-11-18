"""Routes. Each handler takes (body, user, anon, **path params) and returns (status, json-able body).

`user` is None on /api/public/* and otherwise holds the claims API Gateway has already verified.
`anon` is the browser's anonymous id (header x-anon-id), used to link "opened the site" to a later sign-up.
"""
import re
from collections.abc import Callable

from . import cases, db, events


class HttpError(Exception):
    def __init__(self, status: int, code: str):
        super().__init__(code)
        self.status, self.code = status, code


ROUTES: list[tuple[str, re.Pattern, Callable]] = []


def route(method: str, pattern: str):
    def deco(fn):
        ROUTES.append((method, re.compile(f"^{pattern}$"), fn))
        return fn
    return deco


def dispatch(method: str, path: str, body, user, anon=None):
    for m, rx, fn in ROUTES:
        match = rx.match(path)
        if match and m == method:
            return fn(body=body or {}, user=user, anon=anon, **match.groupdict())
    raise HttpError(404, "not_found")


def require_user(user):
    if not user:
        raise HttpError(401, "unauthorized")
    return user


def text(body: dict, key: str, max_len: int, required: bool = True) -> str:
    value = body.get(key)
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise HttpError(400, f"missing_{key}")
        return ""
    if not isinstance(value, str) or len(value) > max_len:
        raise HttpError(400, f"invalid_{key}")
    return value.strip()


def get_case(case_id: str) -> dict:
    case = cases.cases().get(case_id)
    if not case:
        raise HttpError(404, "case_not_found")
    return case


# --- profile ---------------------------------------------------------------------

def profile_key(sub: str) -> dict:
    return {"pk": f"USER#{sub}", "sk": "PROFILE"}


def load_profile(user, anon=None) -> dict:
    """The user's profile; created (and `signed_up` logged) on the first signed-in request."""
    item = db.table().get_item(Key=profile_key(user["sub"])).get("Item")
    if item:
        return item
    item = {**profile_key(user["sub"]), "email": user["email"], "name": user.get("name", ""),
            "created_at": db.now()}
    if anon:
        item["anon_id"] = anon
    db.table().put_item(Item=item)
    events.log("signed_up", user=user["sub"], anon=anon)
    return item


def profile_json(user, item) -> dict:
    return {"email": item["email"], "name": item.get("name", ""), "profession": item.get("profession"),
            "isReviewer": "reviewers" in user["groups"]}


@route("GET", "/api/public/health")
def health(body, user, anon):
    return 200, {"ok": True}


@route("GET", "/api/me")
def me(body, user, anon):
    user = require_user(user)
    return 200, profile_json(user, load_profile(user, anon))


@route("PUT", "/api/me/profession")
def set_profession(body, user, anon):
    user = require_user(user)
    prof = cases.professions().get(body.get("profession"))
    if not prof or prof.get("status") != "live":
        raise HttpError(400, "invalid_profession")
    load_profile(user, anon)
    db.table().update_item(Key=profile_key(user["sub"]), UpdateExpression="SET profession = :p",
                           ExpressionAttributeValues={":p": prof["id"]})
    events.log("profession_chosen", user=user["sub"], value=prof["id"])
    return 200, {"profession": prof["id"]}


# --- events from the browser -------------------------------------------------------

@route("POST", "/api/events")
def client_event(body, user, anon):
    user = require_user(user)
    name = body.get("event")
    if name not in events.CLIENT_EVENTS:
        raise HttpError(400, "invalid_event")
    case_id = body.get("caseId")
    if case_id is not None:
        get_case(case_id)
    events.log(name, user=user["sub"], anon=anon, case_id=case_id, value=text(body, "value", 200, required=False) or None)
    return 200, {"ok": True}
