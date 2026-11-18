"""DynamoDB access. One table, single-table design.

Items (pk / sk):
  USER#<sub>  / PROFILE            email, name, profession, anon_id, created_at
  USER#<sub>  / ATTEMPT#<case_id>  case_id, email, taken_at, deadline, submission, review
                                    (+ gsi1pk=SUBMISSION, gsi1sk=submitted_at once submitted)
  EVENT       / <ts>#<id>          user, anon, event, case_id, value
  FEEDBACK    / <ts>#<sub>         email, case_id, liked, hindered, realism, would_pay
"""
import os
import uuid
from datetime import UTC, datetime, timedelta

import boto3

_table = None


def table():
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    return _table


def reset() -> None:
    """Tests: forget the cached table (a new moto mock per test)."""
    global _table
    _table = None


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def plus_days(ts: str, days: int) -> str:
    t = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ") + timedelta(days=days)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def new_id() -> str:
    return uuid.uuid4().hex[:10]
