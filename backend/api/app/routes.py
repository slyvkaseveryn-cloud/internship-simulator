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


# --- attempts: take a case, submit work ------------------------------------------------

URL_RE = re.compile(r"^https?://[^\s/$.?#][^\s]*$", re.IGNORECASE)


def attempt_key(sub: str, case_id: str) -> dict:
    return {"pk": f"USER#{sub}", "sk": f"ATTEMPT#{case_id}"}


def attempt_json(item: dict) -> dict:
    status = "reviewed" if item.get("review") else "submitted" if item.get("submission") else "taken"
    review = item.get("review")
    if review:
        review = {k: v for k, v in review.items() if k != "reviewer"}
    return {"caseId": item["case_id"], "takenAt": item["taken_at"], "deadline": item["deadline"], "status": status,
            "submission": item.get("submission"), "review": review}


def get_attempt(sub: str, case_id: str) -> dict | None:
    return db.table().get_item(Key=attempt_key(sub, case_id)).get("Item")


@route("POST", "/api/cases/(?P<case_id>[\\w-]+)/take")
def take_case(body, user, anon, case_id):
    user = require_user(user)
    case = get_case(case_id)
    existing = get_attempt(user["sub"], case_id)
    if existing:
        return 200, attempt_json(existing)
    load_profile(user, anon)
    now = db.now()
    item = {**attempt_key(user["sub"], case_id), "case_id": case_id, "taken_at": now,
            "deadline": db.plus_days(now, int(case["deadline_days"])), "email": user["email"]}
    db.table().put_item(Item=item)
    events.log("case_taken", user=user["sub"], case_id=case_id)
    return 201, attempt_json(item)


@route("GET", "/api/cases/(?P<case_id>[\\w-]+)/attempt")
def my_attempt(body, user, anon, case_id):
    user = require_user(user)
    get_case(case_id)
    item = get_attempt(user["sub"], case_id)
    return 200, {"attempt": attempt_json(item) if item else None}


@route("GET", "/api/attempts")
def my_attempts(body, user, anon):
    user = require_user(user)
    items = db.table().query(
        KeyConditionExpression="pk = :pk AND begins_with(sk, :a)",
        ExpressionAttributeValues={":pk": f"USER#{user['sub']}", ":a": "ATTEMPT#"},
    )["Items"]
    items.sort(key=lambda i: i["taken_at"], reverse=True)
    return 200, {"attempts": [attempt_json(i) for i in items]}


@route("POST", "/api/cases/(?P<case_id>[\\w-]+)/submit")
def submit(body, user, anon, case_id):
    user = require_user(user)
    get_case(case_id)
    item = get_attempt(user["sub"], case_id)
    if not item:
        raise HttpError(409, "case_not_taken")
    if item.get("review"):
        raise HttpError(409, "already_reviewed")
    link = text(body, "link", 500)
    if not URL_RE.match(link):
        raise HttpError(400, "invalid_link")
    conclusion = text(body, "conclusion", 2000)
    first = not item.get("submission")
    submission = {"link": link, "conclusion": conclusion, "submitted_at": db.now()}
    # gsi1 is a sparse index: only submitted attempts appear in the reviewers' queue.
    db.table().update_item(
        Key=attempt_key(user["sub"], case_id),
        UpdateExpression="SET submission = :s, gsi1pk = :g, gsi1sk = :t",
        ExpressionAttributeValues={":s": submission, ":g": "SUBMISSION", ":t": submission["submitted_at"]},
    )
    events.log("submitted", user=user["sub"], case_id=case_id, value=None if first else "resubmitted")
    item["submission"] = submission
    return 200, attempt_json(item)


# --- feedback from users (source of quotes and numbers for the report) -------------------

WOULD_PAY = {"yes", "maybe", "no"}


@route("POST", "/api/feedback")
def feedback(body, user, anon):
    user = require_user(user)
    realism = body.get("realism")
    if not isinstance(realism, int) or isinstance(realism, bool) or not 1 <= realism <= 5:
        raise HttpError(400, "invalid_realism")
    would_pay = body.get("wouldPay")
    if would_pay not in WOULD_PAY:
        raise HttpError(400, "invalid_wouldPay")
    case_id = body.get("caseId") or None
    if case_id:
        get_case(case_id)
    ts = db.now()
    item = {"pk": "FEEDBACK", "sk": f"{db.now_precise()}#{user['sub']}", "ts": ts, "sub": user["sub"],
            "email": user["email"], "realism": realism, "would_pay": would_pay,
            "liked": text(body, "liked", 2000, required=False), "hindered": text(body, "hindered", 2000, required=False)}
    if case_id:
        item["case_id"] = case_id
    db.table().put_item(Item=item)
    events.log("feedback_sent", user=user["sub"], case_id=case_id, value=str(realism))
    return 201, {"ok": True}


# --- anonymous events (before sign-in) ----------------------------------------------------

ANON_RE = re.compile(r"^[A-Za-z0-9-]{8,64}$")


@route("POST", "/api/public/events")
def public_event(body, user, anon):
    if body.get("event") not in events.PUBLIC_EVENTS:
        raise HttpError(400, "invalid_event")
    if not anon or not ANON_RE.match(anon):
        raise HttpError(400, "invalid_anon")
    events.log(body["event"], anon=anon)
    return 200, {"ok": True}


# --- reviewers: queue of submissions, writing a review -------------------------------------

def require_reviewer(user):
    user = require_user(user)
    if "reviewers" not in user["groups"]:
        raise HttpError(403, "forbidden")
    return user


@route("GET", "/api/review/submissions")
def review_queue(body, user, anon):
    require_reviewer(user)
    items, kw = [], {"IndexName": "gsi1", "KeyConditionExpression": "gsi1pk = :g",
                     "ExpressionAttributeValues": {":g": "SUBMISSION"}, "ScanIndexForward": False}
    while True:
        r = db.table().query(**kw)
        items += r["Items"]
        if "LastEvaluatedKey" not in r:
            break
        kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]
    titles = {cid: c["title"] for cid, c in cases.cases().items()}
    out = [{**attempt_json(i), "userId": i["pk"].removeprefix("USER#"), "email": i.get("email", ""),
            "caseTitle": titles.get(i["case_id"], i["case_id"])} for i in items]
    out.sort(key=lambda a: a["status"] == "reviewed")  # waiting for a review first, newest first within
    return 200, {"submissions": out}


@route("POST", "/api/review/(?P<user_id>[\\w-]+)/(?P<case_id>[\\w-]+)")
def write_review(body, user, anon, user_id, case_id):
    reviewer = require_reviewer(user)
    get_case(case_id)
    item = get_attempt(user_id, case_id)
    if not item or not item.get("submission"):
        raise HttpError(404, "submission_not_found")
    review = {"good": text(body, "good", 4000), "fix": text(body, "fix", 4000), "next": text(body, "next", 4000),
              "reviewed_at": db.now(), "reviewer": reviewer["email"]}
    first = not item.get("review")
    db.table().update_item(Key=attempt_key(user_id, case_id), UpdateExpression="SET review = :r",
                           ExpressionAttributeValues={":r": review})
    # user = the student: "got a review" is a step of *their* funnel.
    events.log("review_sent", user=user_id, case_id=case_id, value=None if first else "edited")
    item["review"] = review
    return 200, attempt_json(item)
