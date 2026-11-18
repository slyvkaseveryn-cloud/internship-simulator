import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { formatDate, STATUS_LABEL, type Attempt } from '../attempts'
import { loadCases, type Case } from '../cases'

export default function MyCases() {
  const [attempts, setAttempts] = useState<Attempt[] | null>(null)
  const [cases, setCases] = useState<Record<string, Case>>({})
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api<{ attempts: Attempt[] }>('/attempts'), loadCases()]).then(([a, c]) => {
      setAttempts(a.attempts)
      setCases(Object.fromEntries(c.map((x) => [x.id, x])))
    }).catch(() => setError('Не вдалося завантажити твої кейси. Онови сторінку.'))
  }, [])

  if (error) return <p className="error">{error}</p>
  if (!attempts) return <p>Завантаження…</p>
  return (
    <section>
      <h1>Мої кейси</h1>
      {attempts.length === 0 && <p>Тут поки порожньо. <Link to="/cases">Обрати кейс</Link></p>}
      <div className="list">
        {attempts.map((a) => (
          <Link key={a.caseId} to={`/cases/${a.caseId}`} className="card case-card">
            <b>{cases[a.caseId]?.title ?? a.caseId}</b>
            <span className={`chip status-${a.status}`}>{STATUS_LABEL[a.status]}</span>
            <span className="meta">
              {a.status === 'taken' ? `Дедлайн: ${formatDate(a.deadline)}` :
                a.submission ? `Здано ${formatDate(a.submission.submitted_at)}` : ''}
            </span>
          </Link>
        ))}
      </div>
    </section>
  )
}
