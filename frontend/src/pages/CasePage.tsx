import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { track } from '../api'
import { daysWord, fileUrl, loadBrief, loadCases, type Case } from '../cases'
import CaseWork from './CaseWork'

export default function CasePage() {
  const { id } = useParams()
  const [c, setCase] = useState<Case | null | undefined>(undefined)
  const [brief, setBrief] = useState<{ letter: string; about: string } | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    loadCases().then((all) => {
      const found = all.find((x) => x.id === id) ?? null
      setCase(found)
      if (found) {
        track('case_viewed', found.id)
        loadBrief(found).then(setBrief).catch(() => setError('Не вдалося завантажити лист. Онови сторінку.'))
      }
    }).catch(() => setError('Не вдалося завантажити кейс. Онови сторінку.'))
  }, [id])

  if (c === undefined) return <p>{error || 'Завантаження…'}</p>
  if (c === null) return <p>Кейс не знайдено. <Link to="/cases">До кейсів</Link></p>

  return (
    <article className="case">
      <p><Link to={`/roles/${c.profession}`}>← {c.track}</Link></p>
      <h1>{c.title}</h1>
      <p className="muted">{c.company} · {c.level}</p>

      <div className="facts">
        <div><span className="muted">Час</span><b>{c.time_estimate}</b></div>
        <div className="deadline">
          <span className="muted">Дедлайн</span><b>{daysWord(c.deadline_days)}</b>
          <small>Не встиг? Нічого не заблокується: здати можна й пізніше, рев'ю буде так само.</small>
        </div>
        <div><span className="muted">Інструменти</span><b>{c.tools}</b></div>
      </div>

      <Link to={`/feedback?case=${c.id}`} className="btn ghost feedback-case">Залишити відгук про кейс</Link>

      <CaseWork c={c} />

      <div className="card similar">
        <span className="chip">Схожі тестові</span>
        <p>{c.similar}</p>
      </div>

      <h2>Лист від менеджера</h2>
      {error && <p className="error">{error}</p>}
      {brief ? <div className="card letter" dangerouslySetInnerHTML={{ __html: brief.letter }} /> : !error && <p>Завантаження…</p>}

      <div className="card first-step">
        <b>Перший крок на 20 хвилин</b>
        <p>{c.first_step}</p>
      </div>

      <h2>Файли</h2>
      <ul className="files">
        {[c.brief, ...c.files.map((f) => f.name)].map((name) => {
          const f = c.files.find((x) => x.name === name)
          return (
            <li key={name}>
              <a href={fileUrl(c, name)} download>{name}</a>
              <span className="muted">{f ? f.caption.replace(`${name}: `, '') : 'лист і опис даних'}</span>
            </li>
          )
        })}
      </ul>

      {brief?.about && (
        <details className="card">
          <summary>Про продукт і дані</summary>
          <div dangerouslySetInnerHTML={{ __html: brief.about }} />
        </details>
      )}

      <p className="muted">Що перевіряє кейс: {c.skills.join(', ')}.</p>
    </article>
  )
}
