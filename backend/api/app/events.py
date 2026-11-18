"""Funnel events. Every step of the user's path is one item under pk=EVENT."""
from . import db

# Events the browser may send itself. Everything else is written by the API when the action happens.
CLIENT_EVENTS = {"case_viewed", "donate_clicked"}
PUBLIC_EVENTS = {"opened"}


def log(event: str, user: str | None = None, anon: str | None = None, case_id: str | None = None,
        value: str | None = None) -> None:
    item = {"pk": "EVENT", "sk": f"{db.now_precise()}#{db.new_id()}", "ts": db.now(), "event": event}
    for key, val in (("user", user), ("anon", anon), ("case_id", case_id), ("value", value)):
        if val:
            item[key] = val
    db.table().put_item(Item=item)
