import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { daysWord, loadCases, loadProfessions, type Case, type Profession } from '../cases'

export default function RoleCases() {
  const { role } = useParams()
  const [cases, setCases] = useState<Case[] | null>(null)
  const [prof, setProf] = useState<Profession | null>(null)

  useEffect(() => {
    Promise.all([loadCases(), loadProfessions()]).then(([c, p]) => {
      setCases(c.filter((x) => x.profession === role))
      setProf(p.find((x) => x.id === role) ?? null)
    }).catch(() => setCases([]))
  }, [role])

  if (!cases) return <p>Завантаження…</p>
  return (
    <section>
      <p><Link to="/cases">← Усі напрями</Link></p>
      <h1>{prof ? `${prof.emoji} ${prof.title}` : 'Кейси'}</h1>
      {cases.length === 0 && <p>Тут поки немає кейсів.</p>}
      <div className="list">
        {cases.map((c) => (
          <Link key={c.id} to={`/cases/${c.id}`} className="card case-card">
            <b>{c.title}</b>
            <span className="muted">{c.company}</span>
            <span>{c.teaser}</span>
            <span className="meta">⏱ {c.time_estimate} · дедлайн {daysWord(c.deadline_days)}</span>
          </Link>
        ))}
      </div>
    </section>
  )
}
