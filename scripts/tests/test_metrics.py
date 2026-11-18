import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import metrics  # noqa: E402

PROFILES = [
    {"pk": "USER#real", "email": "olya@gmail.com", "anon_id": "a-real"},
    {"pk": "USER#team", "email": "sev@gmail.com", "anon_id": "a-team"},
    {"pk": "USER#e2e", "email": "e2e-1a2b@example.com", "anon_id": "a-e2e"},
    {"pk": "USER#extra", "email": "lev@ucu.edu.ua"},
]


def ev(event, user=None, anon=None, case_id=None, value=None):
    return {"event": event, "user": user, "anon": anon, "case_id": case_id, "value": value, "sk": "x"}


def test_test_emails():
    assert metrics.is_test_email("e2e-123@example.com")
    assert metrics.is_test_email("me+test@gmail.com")
    assert not metrics.is_test_email("olya@gmail.com")


def test_team_test_and_extra_accounts_are_excluded_with_their_browsers():
    subs, anons = metrics.excluded_ids(PROFILES, {"team"}, {"lev@ucu.edu.ua"})
    assert subs == {"team", "e2e", "extra"} and anons == {"a-team", "a-e2e"}
    events = [ev("opened", anon="a-real"), ev("opened", anon="a-team"), ev("opened", anon="a-stranger"),
              ev("signed_up", "real", "a-real"), ev("signed_up", "team", "a-team"), ev("case_taken", "e2e")]
    kept = metrics.clean_events(events, subs, anons)
    assert [(e["event"], e["user"] or e["anon"]) for e in kept] == [
        ("opened", "a-real"), ("opened", "a-stranger"), ("signed_up", "real")]


def test_funnel_counts_people_not_events():
    events = [ev("opened", anon="a1"), ev("opened", anon="a1"), ev("opened", anon="a2"),
              ev("signed_up", "u1"), ev("case_taken", "u1", case_id="01"), ev("case_taken", "u1", case_id="02"),
              ev("submitted", "u1", case_id="01"), ev("submitted", "u1", case_id="01", value="resubmitted")]
    f = {e: n for e, _, n in metrics.funnel(events)}
    assert f["opened"] == 2 and f["signed_up"] == 1 and f["case_taken"] == 1 and f["submitted"] == 1
    s = metrics.summary(events, [{"realism": 4, "would_pay": "yes"}, {"realism": 5, "would_pay": "no"}])
    assert s["cases_taken"] == 2 and s["cases_submitted"] == 1 and s["avg_realism"] == 4.5
    assert s["would_pay"] == {"yes": 1, "no": 1}


def test_stub_donate_clicks_do_not_count():
    events = [ev("donate_clicked", "u1", value="stub"), ev("donate_clicked", "u2")]
    assert metrics.summary(events, [])["donate_clicks_people"] == 1


def test_automated_test_browsers_are_excluded():
    kept = metrics.clean_events([ev("opened", anon="e2e-abc123"), ev("opened", anon="0b5f8e2a-1111")], set(), set())
    assert [e["anon"] for e in kept] == ["0b5f8e2a-1111"]
