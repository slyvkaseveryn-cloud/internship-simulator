import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError, post } from '../api'
import { formatDate, STATUS_LABEL, type Attempt } from '../attempts'
import { daysWord, type Case } from '../cases'

/** The "take the case → submit work" block on a case page. */
export default function CaseWork({ c, onAttempt }: { c: Case; onAttempt?: (a: Attempt | null) => void }) {
  const [attempt, setAttempt] = useState<Attempt | null | undefined>(undefined)
  const [editing, setEditing] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api<{ attempt: Attempt | null }>(`/cases/${c.id}/attempt`)
      .then((r) => setAttempt(r.attempt))
      .catch(() => setError('Не вдалося завантажити статус кейсу. Онови сторінку.'))
  }, [c.id])

  useEffect(() => {
    if (attempt !== undefined) onAttempt?.(attempt)
  }, [attempt, onAttempt])

  async function take() {
    setError('')
    try {
      setAttempt(await post<Attempt>(`/cases/${c.id}/take`, {}))
    } catch {
      setError('Не вдалося взяти кейс. Спробуй ще раз.')
    }
  }

  if (attempt === undefined) return error ? <p className="error">{error}</p> : null

  if (attempt === null) {
    return (
      <div className="card take">
        <p>Після «Беру кейс» почнеться відлік: {daysWord(c.deadline_days)}, щоб здати роботу.</p>
        <button className="btn" onClick={take}>Беру кейс</button>
        {error && <p className="error">{error}</p>}
      </div>
    )
  }

  const overdue = attempt.status === 'taken' && new Date(attempt.deadline) < new Date()
  return (
    <div className="card status-card">
      <div className="status-row">
        <span className={`chip status-${attempt.status}`}>{STATUS_LABEL[attempt.status]}</span>
        {attempt.status === 'taken' && (
          <span className={overdue ? 'error' : 'muted'}>Дедлайн: {formatDate(attempt.deadline)}</span>
        )}
      </div>
      {overdue && <p className="muted">Дедлайн минув, але неідеальна здача краща за жодну. Здай те, що є.</p>}

      {attempt.submission && !editing && (
        <div className="submission">
          <p><span className="muted">Робота:</span> <a href={attempt.submission.link} target="_blank" rel="noreferrer">{attempt.submission.link}</a></p>
          <p className="pre">{attempt.submission.conclusion}</p>
          <p className="muted small">Здано {formatDate(attempt.submission.submitted_at)}</p>
          {attempt.status === 'submitted' && (
            <button className="link" onClick={() => setEditing(true)}>Змінити здачу</button>
          )}
        </div>
      )}

      {(attempt.status === 'taken' || editing) && (
        <SubmitForm caseId={c.id} initial={attempt.submission} onDone={(a) => { setAttempt(a); setEditing(false) }}
          onCancel={editing ? () => setEditing(false) : undefined} />
      )}

      {attempt.status !== 'taken' && (
        <p className="small"><Link to="/my">Усі мої кейси</Link></p>
      )}
    </div>
  )
}

function SubmitForm(props: { caseId: string; initial: Attempt['submission']; onDone: (a: Attempt) => void; onCancel?: () => void }) {
  const [link, setLink] = useState(props.initial?.link ?? '')
  const [conclusion, setConclusion] = useState(props.initial?.conclusion ?? '')
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  function check(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (!/^https?:\/\/\S+$/i.test(link.trim())) {
      setError('Встав посилання, що починається з https:// (GitHub, Google Doc, Colab, Notion…).')
      return
    }
    setConfirming(true)
  }

  async function send() {
    setBusy(true)
    try {
      props.onDone(await post<Attempt>(`/cases/${props.caseId}/submit`, { link: link.trim(), conclusion }))
    } catch (err) {
      const code = err instanceof ApiError ? err.code : ''
      setError(code === 'invalid_link' ? 'Посилання виглядає неправильним.' : 'Не вдалося здати. Спробуй ще раз.')
      setConfirming(false)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="form-inline" onSubmit={check}>
      <h3>Здати роботу</h3>
      <label className="field">
        <span>Посилання на роботу</span>
        <input type="url" inputMode="url" required value={link} onChange={(e) => { setLink(e.target.value); setConfirming(false) }}
          placeholder="https://github.com/…" />
        <small>Перевір, що доступ відкритий для всіх, хто має посилання.</small>
      </label>
      <label className="field">
        <span>Короткий висновок для менеджера</span>
        <textarea required rows={5} maxLength={2000} value={conclusion} onChange={(e) => { setConclusion(e.target.value); setConfirming(false) }}
          placeholder="Висновок першим, 5–10 речень, без формул." />
      </label>
      {error && <p className="error">{error}</p>}
      {confirming ? (
        <div className="confirm">
          <p>Здаємо? Після рев'ю змінити роботу вже не вийде.</p>
          <div className="actions">
            <button type="button" className="btn" onClick={send} disabled={busy}>{busy ? 'Зачекай…' : 'Так, здаю'}</button>
            <button type="button" className="btn ghost" onClick={() => setConfirming(false)}>Ще ні</button>
          </div>
        </div>
      ) : (
        <div className="actions">
          <button className="btn" type="submit">Здати</button>
          {props.onCancel && <button type="button" className="btn ghost" onClick={props.onCancel}>Скасувати</button>}
        </div>
      )}
    </form>
  )
}
