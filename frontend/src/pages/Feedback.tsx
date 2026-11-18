import { useEffect, useState, type FormEvent } from 'react'
import { Link, useLocation, useSearchParams } from 'react-router-dom'
import { api, post } from '../api'
import type { Attempt } from '../attempts'
import { loadCases, type Case } from '../cases'
import Donate from '../Donate'

const PAY = [
  { value: 'yes', label: 'Так' },
  { value: 'maybe', label: 'Можливо' },
  { value: 'no', label: 'Ні' },
]

/** A fresh form on every navigation, e.g. «Залишити відгук» in the menu right after sending one. */
export default function Feedback() {
  const location = useLocation()
  return <FeedbackForm key={location.key} />
}

function FeedbackForm() {
  const [params] = useSearchParams()
  const caseId = params.get('case') ?? ''
  const [c, setCase] = useState<Case | null>(null)
  const [liked, setLiked] = useState('')
  const [hindered, setHindered] = useState('')
  const [realism, setRealism] = useState(0)
  const [wouldPay, setWouldPay] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [sent, setSent] = useState(false)
  const [reviewed, setReviewed] = useState(false)

  useEffect(() => {
    api<{ attempts: Attempt[] }>('/attempts')
      .then((r) => setReviewed(r.attempts.some((a) => a.status === 'reviewed')))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (caseId) loadCases().then((all) => setCase(all.find((x) => x.id === caseId) ?? null)).catch(() => {})
  }, [caseId])

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!realism || !wouldPay) {
      setError('Обери оцінку від 1 до 5 і відповідь про рев’ю.')
      return
    }
    setBusy(true)
    setError('')
    try {
      await post('/feedback', { liked, hindered, realism, wouldPay, caseId: c ? c.id : undefined })
      setSent(true)
    } catch {
      setError('Не вдалося надіслати. Спробуй ще раз.')
    } finally {
      setBusy(false)
    }
  }

  if (sent) {
    return (
      <section className="card">
        <h1>Дякуємо!</h1>
        <p>Твій відгук допоможе зробити кейси ближчими до справжніх тестових.</p>
        <p><Link to="/my">До моїх кейсів</Link></p>
        {reviewed && <Donate caseId={c?.id} />}
      </section>
    )
  }

  return (
    <form className="card form wide" onSubmit={submit}>
      <h1>Відгук</h1>
      {c ? <p className="muted">Кейс: {c.title}</p> : <p className="muted">Про сайт і кейси загалом. Можна й до того, як береш кейс.</p>}
      <label className="field">
        <span>Що сподобалось?</span>
        <textarea rows={3} maxLength={2000} value={liked} onChange={(e) => setLiked(e.target.value)} />
      </label>
      <label className="field">
        <span>Що заважало?</span>
        <textarea rows={3} maxLength={2000} value={hindered} onChange={(e) => setHindered(e.target.value)} />
      </label>
      <fieldset className="field">
        <legend>Наскільки це схоже на справжнє тестове завдання?</legend>
        <div className="scale" role="radiogroup">
          {[1, 2, 3, 4, 5].map((n) => (
            <label key={n} className={`pill ${realism === n ? 'on' : ''}`}>
              <input type="radio" name="realism" value={n} checked={realism === n} onChange={() => setRealism(n)} />
              {n}
            </label>
          ))}
        </div>
        <small>1 — зовсім не схоже, 5 — як справжнє</small>
      </fieldset>
      <fieldset className="field">
        <legend>Чи заплатив би ти за детальне рев'ю своєї роботи?</legend>
        <div className="scale" role="radiogroup">
          {PAY.map((p) => (
            <label key={p.value} className={`pill ${wouldPay === p.value ? 'on' : ''}`}>
              <input type="radio" name="wouldPay" value={p.value} checked={wouldPay === p.value} onChange={() => setWouldPay(p.value)} />
              {p.label}
            </label>
          ))}
        </div>
      </fieldset>
      {error && <p className="error" role="alert">{error}</p>}
      <button className="btn" type="submit" disabled={busy}>{busy ? 'Зачекай…' : 'Надіслати відгук'}</button>
    </form>
  )
}
