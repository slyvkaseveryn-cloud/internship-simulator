"""Routes. Each handler returns (status, json-able body)."""
import re


class HttpError(Exception):
    def __init__(self, status: int, code: str):
        super().__init__(code)
        self.status, self.code = status, code


ROUTES: list[tuple[str, re.Pattern, callable]] = []


def route(method: str, pattern: str):
    def deco(fn):
        ROUTES.append((method, re.compile(f"^{pattern}$"), fn))
        return fn
    return deco


def dispatch(method: str, path: str, body, user):
    for m, rx, fn in ROUTES:
        match = rx.match(path)
        if match and m == method:
            return fn(body=body, user=user, **match.groupdict())
    raise HttpError(404, "not_found")


def require_user(user):
    if not user:
        raise HttpError(401, "unauthorized")
    return user


@route("GET", "/api/public/health")
def health(body, user):
    return 200, {"ok": True}


@route("GET", "/api/me")
def me(body, user):
    user = require_user(user)
    return 200, {"email": user["email"], "isReviewer": "reviewers" in user["groups"]}
