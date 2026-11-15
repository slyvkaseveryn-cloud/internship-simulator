"""HTML-дашборд продукту для автора: воронка, ключові метрики, кейси, оцінки.

Запуск окремо: python -m telegram_bot.report > dashboard.html. У боті: команда /report.
"""
from datetime import datetime
from html import escape

from .storage import FMT, Storage

STYLE = """
:root { color-scheme: light; --bg:#f6f5f2; --surface:#fcfcfb; --ink:#0b0b0b; --ink-2:#52514e; --muted:#8a8984;
  --line:#e4e2dc; --series:#2a78d6; --track:#ecebe6; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { color-scheme: dark; --bg:#111110; --surface:#1a1a19;
  --ink:#f0efec; --ink-2:#c3c2b7; --muted:#8f8e86; --line:#2c2c2a; --series:#3987e5; --track:#262624; } }
:root[data-theme="dark"] { color-scheme: dark; --bg:#111110; --surface:#1a1a19; --ink:#f0efec; --ink-2:#c3c2b7;
  --muted:#8f8e86; --line:#2c2c2a; --series:#3987e5; --track:#262624; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 960px; margin: 0 auto; padding: 32px 16px 64px; }
h1 { font-size: 24px; margin: 0 0 4px; } h2 { font-size: 16px; margin: 0 0 16px; }
.sub { color: var(--ink-2); margin: 0 0 28px; }
.tiles { display:grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 24px; }
.tile, .card { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 16px; }
.tile .v { font-size: 28px; font-weight: 600; font-variant-numeric: tabular-nums; }
.tile .l { color: var(--ink-2); font-size: 13px; }
.card { margin-bottom: 16px; overflow-x: auto; }
.row { display:grid; grid-template-columns: 170px 1fr 110px; gap: 12px; align-items:center; padding: 6px 0; }
.bar { height: 14px; background: var(--track); border-radius: 4px; position: relative; }
.bar span { position:absolute; inset:0 auto 0 0; background: var(--series); border-radius: 4px; min-width: 2px; }
.bar:hover span { filter: brightness(1.1); }
.num { font-variant-numeric: tabular-nums; text-align:right; color: var(--ink-2); font-size: 13px; }
.num b { color: var(--ink); }
table { width:100%; border-collapse: collapse; font-size: 14px; }
th, td { text-align:left; padding: 8px 6px; border-bottom: 1px solid var(--line); }
th { color: var(--ink-2); font-weight: 500; font-size: 13px; }
td.n { text-align:right; font-variant-numeric: tabular-nums; }
.note { color: var(--muted); font-size: 13px; margin-top: 8px; }
@media (max-width: 560px) { .row { grid-template-columns: 1fr 90px; } .row .bar { grid-column: 1 / -1; order: 3; } }
"""


def _hours_between(a: str, b: str) -> float:
    return (datetime.strptime(b, FMT) - datetime.strptime(a, FMT)).total_seconds() / 3600


def build_report(db: Storage, cases: dict, professions: dict | None = None) -> str:
    q = db.db.execute
    funnel = db.funnel()
    top = funnel[0][1] or 1

    rows = []
    prev = None
    for label, n in funnel:
        share = n / top
        step = f" · {n * 100 // prev}% від попер." if prev else ""
        rows.append(
            f'<div class="row"><div>{escape(label)}</div>'
            f'<div class="bar" title="{escape(label)}: {n} людей ({share:.0%} від тих, хто відкрив бота)">'
            f'<span style="width:{share * 100:.1f}%"></span></div>'
            f'<div class="num"><b>{n}</b>{step}</div></div>'
        )
        prev = n or None

    subs = q("SELECT s.*, a.started_at FROM submissions s JOIN attempts a ON a.id = s.attempt_id").fetchall()
    hours = sorted(_hours_between(s["started_at"], s["submitted_at"]) for s in subs)
    median_h = f"{hours[len(hours) // 2]:.0f} год" if hours else "—"
    ratings = [s["rating"] for s in subs if s["rating"]]
    avg_rating = f"{sum(ratings) / len(ratings):.1f} / 5" if ratings else "—"
    pending = sum(1 for s in subs if not s["reviewed_at"])
    users = q("SELECT COUNT(*) FROM users").fetchone()[0]

    tiles = [
        (users, "людей відкрили бота"),
        (len(subs), "здач усього"),
        (pending, "чекають на рев'ю"),
        (median_h, "медіана від старту до здачі"),
        (avg_rating, "оцінка «схоже на справжнє»"),
    ]
    tiles_html = "".join(f'<div class="tile"><div class="v">{v}</div><div class="l">{escape(label)}</div></div>' for v, label in tiles)

    case_rows = []
    for cid, case in cases.items():
        taken = q("SELECT COUNT(DISTINCT user_id) FROM attempts WHERE case_id=?", (cid,)).fetchone()[0]
        done = q("SELECT COUNT(DISTINCT user_id) FROM submissions WHERE case_id=?", (cid,)).fetchone()[0]
        rated = q("SELECT AVG(rating) FROM submissions WHERE case_id=? AND rating IS NOT NULL", (cid,)).fetchone()[0]
        rate = f"{done * 100 // taken}%" if taken else "—"
        case_rows.append(
            f"<tr><td>{escape(case['title'])}</td><td class='n'>{taken}</td><td class='n'>{done}</td>"
            f"<td class='n'>{rate}</td><td class='n'>{f'{rated:.1f}' if rated else '—'}</td></tr>"
        )

    professions = professions or {}
    chosen = dict(q("SELECT value, COUNT(DISTINCT user_id) FROM events WHERE event='profession_chosen' GROUP BY value").fetchall())
    votes = dict(db.track_votes())
    prof_rows = "".join(
        f"<tr><td>{escape(p['title'])}</td><td>{'працює' if p['status'] == 'live' else 'незабаром'}</td>"
        f"<td class='n'>{chosen.get(pid, 0)}</td><td class='n'>{votes.get(pid, 0) if p['status'] != 'live' else '—'}</td></tr>"
        for pid, p in professions.items()
    )

    recent = q("SELECT e.ts, e.event, e.case_id, u.username FROM events e LEFT JOIN users u USING(user_id) "
               "ORDER BY e.id DESC LIMIT 15").fetchall()
    recent_rows = "".join(
        f"<tr><td>{escape(r['ts'][5:16])}</td><td>{escape('@' + r['username'] if r['username'] else '—')}</td>"
        f"<td>{escape(r['event'])}</td><td>{escape(r['case_id'] or '')}</td></tr>"
        for r in recent
    )

    return f"""<!doctype html><html lang="uk"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Дашборд симулятора</title>
<style>{STYLE}</style></head><body><main>
<h1>Дашборд симулятора стажувань</h1>
<p class="sub">Згенеровано {datetime.now():%d.%m.%Y о %H:%M}. Усі числа — унікальні люди.</p>
<div class="tiles">{tiles_html}</div>
<section class="card"><h2>Воронка</h2>{''.join(rows)}
<p class="note">Головна метрика зараз: частка тих, хто взяв кейс і здав роботу.</p></section>
<section class="card"><h2>Кейси</h2><table><thead><tr><th>Кейс</th><th>Взяли</th><th>Здали</th><th>Конверсія</th><th>Оцінка</th></tr></thead>
<tbody>{''.join(case_rows)}</tbody></table></section>
<section class="card"><h2>Професії</h2><table><thead><tr><th>Напрям</th><th>Статус</th><th>Обрали</th><th>Хочуть</th></tr></thead>
<tbody>{prof_rows}</tbody></table>
<p class="note">«Хочуть» — натиснули «🔔 Хочу цей напрям». Новий напрям робимо там, де цих людей найбільше.</p></section>
<section class="card"><h2>Останні події</h2><table><thead><tr><th>Час</th><th>Хто</th><th>Подія</th><th>Кейс</th></tr></thead>
<tbody>{recent_rows}</tbody></table></section>
</main></body></html>"""


if __name__ == "__main__":
    from .config import CASES, DB_PATH, PROFESSIONS

    print(build_report(Storage(DB_PATH), CASES, PROFESSIONS))
