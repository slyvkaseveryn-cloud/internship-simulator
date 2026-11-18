#!/usr/bin/env python3
"""Funnel and feedback numbers for the course report, straight from DynamoDB.

    .venv/bin/python scripts/metrics.py                 # funnel in people, printed
    .venv/bin/python scripts/metrics.py --csv out/      # + funnel.csv, feedback.csv, events.csv

Needs read access to the AWS account (the owner's credentials). Excluded from every number:
  - members of the Cognito group `reviewers` (the team),
  - test accounts: emails at example.com/.org/.net, starting with `e2e-` or `test`, or containing `+test`,
  - any email passed with --exclude (repeatable),
  - anonymous visits from browsers that later signed in as one of the above,
  - anonymous visits from automated test browsers (anonymous id starting with `e2e-`).
"""
import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

REGION = "eu-central-1"
TABLE = "internship-simulator"
POOL_NAME = "internship-simulator"

# (event, label). "opened" counts anonymous browsers, everything else counts signed-in people.
FUNNEL = [
    ("opened", "Opened the site"),
    ("signed_up", "Signed up"),
    ("profession_chosen", "Chose a role"),
    ("case_viewed", "Viewed a case"),
    ("case_taken", "Took a case"),
    ("submitted", "Submitted work"),
    ("review_sent", "Got a review"),
    ("feedback_sent", "Left feedback"),
]

TEST_EMAIL = re.compile(r"(@example\.(com|org|net)$)|(^e2e-)|(^test)|(\+test)", re.IGNORECASE)


def is_test_email(email: str) -> bool:
    return bool(TEST_EMAIL.search(email or ""))


def excluded_ids(profiles: list[dict], team_subs: set[str], extra_emails: set[str]) -> tuple[set[str], set[str]]:
    """Subs and anonymous browser ids that must not be counted."""
    subs, anons = set(team_subs), set()
    for p in profiles:
        sub = p["pk"].removeprefix("USER#")
        email = (p.get("email") or "").lower()
        if sub in team_subs or is_test_email(email) or email in extra_emails:
            subs.add(sub)
            if p.get("anon_id"):
                anons.add(p["anon_id"])
    return subs, anons


def clean_events(events: list[dict], subs: set[str], anons: set[str]) -> list[dict]:
    """Drop the team's and test accounts' events.

    review_sent is written with user = the student who got the review, so it is kept for real students.
    """
    return [e for e in events if e.get("user") not in subs and not (e.get("anon") and e.get("anon") in anons)
            and not str(e.get("anon") or "").startswith("e2e-")]


def funnel(events: list[dict]) -> list[tuple[str, str, int]]:
    rows = []
    for event, label in FUNNEL:
        key = "anon" if event == "opened" else "user"
        people = {e.get(key) for e in events if e["event"] == event and e.get(key)}
        rows.append((event, label, len(people)))
    return rows


def summary(events: list[dict], feedback: list[dict]) -> dict:
    realism = [int(f["realism"]) for f in feedback]
    taken = {(e["user"], e.get("case_id")) for e in events if e["event"] == "case_taken"}
    submitted = {(e["user"], e.get("case_id")) for e in events if e["event"] == "submitted"}
    return {
        "feedback_count": len(feedback),
        "avg_realism": round(sum(realism) / len(realism), 2) if realism else None,
        "would_pay": dict(Counter(f["would_pay"] for f in feedback)),
        "cases_taken": len(taken),
        "cases_submitted": len(submitted & taken),
        "donate_clicks_people": len({e["user"] for e in events if e["event"] == "donate_clicked" and e.get("value") != "stub"}),
    }


# --- AWS --------------------------------------------------------------------------------------

def load(exclude: set[str]):
    import boto3
    from boto3.dynamodb.conditions import Attr, Key

    table = boto3.resource("dynamodb", region_name=REGION).Table(TABLE)

    def query(pk):
        items, kw = [], {"KeyConditionExpression": Key("pk").eq(pk)}
        while True:
            r = table.query(**kw)
            items += r["Items"]
            if "LastEvaluatedKey" not in r:
                return items
            kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]

    profiles, kw = [], {"FilterExpression": Attr("sk").eq("PROFILE")}
    while True:
        r = table.scan(**kw)
        profiles += r["Items"]
        if "LastEvaluatedKey" not in r:
            break
        kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]

    idp = boto3.client("cognito-idp", region_name=REGION)
    pool = next(p["Id"] for p in idp.list_user_pools(MaxResults=60)["UserPools"] if p["Name"] == POOL_NAME)
    team = set()
    for page in idp.get_paginator("list_users_in_group").paginate(UserPoolId=pool, GroupName="reviewers"):
        for u in page["Users"]:
            team |= {a["Value"] for a in u["Attributes"] if a["Name"] == "sub"}

    subs, anons = excluded_ids(profiles, team, exclude)
    events = clean_events(query("EVENT"), subs, anons)
    feedback = [f for f in query("FEEDBACK") if f.get("sub") not in subs]
    return events, feedback, len(subs)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=Path, help="directory for funnel.csv, feedback.csv, events.csv")
    ap.add_argument("--exclude", action="append", default=[], help="email to leave out (repeatable)")
    args = ap.parse_args(argv)

    events, feedback, n_excluded = load({e.lower() for e in args.exclude})
    rows = funnel(events)

    print(f"Funnel (people; {n_excluded} team/test accounts excluded)")
    prev = None
    for _, label, n in rows:
        step = f"  {n * 100 // prev}% of previous" if prev else ""
        print(f"  {label:<18} {n:>5}{step}")
        prev = n or None
    s = summary(events, feedback)
    print(f"\nCases taken: {s['cases_taken']}, submitted: {s['cases_submitted']}")
    print(f"Feedback: {s['feedback_count']}, average realism: {s['avg_realism']}, would pay: {s['would_pay']}")
    print(f"People who clicked «Support volunteers»: {s['donate_clicks_people']}")

    if args.csv:
        args.csv.mkdir(parents=True, exist_ok=True)
        write_csv(args.csv / "funnel.csv", [{"step": label, "event": e, "people": n} for e, label, n in rows],
                  ["step", "event", "people"])
        write_csv(args.csv / "feedback.csv", sorted(feedback, key=lambda f: f["ts"]),
                  ["ts", "email", "case_id", "realism", "would_pay", "liked", "hindered"])
        write_csv(args.csv / "events.csv", sorted(events, key=lambda e: e["sk"]),
                  ["ts", "event", "user", "anon", "case_id", "value"])
        print(f"\nCSV written to {args.csv}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
