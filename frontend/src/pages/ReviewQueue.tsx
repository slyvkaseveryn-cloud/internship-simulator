import { useEffect, useState, type FormEvent } from 'react'
import { api, post } from '../api'
import { formatDate, STATUS_LABEL, type Attempt } from '../attempts'
import { useMe } from '../useMe'

type Item = Attempt & { userId: string; email: string; caseTitle: string }

export default function ReviewQueue() {
  const { me } = useMe()
  const [items, setItems] = useState<Item[] | null>(null)
  const [error, setError] = useState('')
  const [onlyPending, setOnlyPending] = useState(true)

  useEffect(() => {
    if (!me?.isReviewer) return
    api<{ submissions: Item[] }>('/review/submissions').then((r) => setItems(r.submissions))
      .catch(() => setError('Не вдалося завантажити здачі.'))
  }, [me?.isReviewer])

  if (!me) return <p>Завантаження…</p>
  if (!me.isReviewer) return <p>Ця сторінка лише для рецензентів. Якщо ти рецензент, вийди й увійди знову.</p>
  if (error) return <p className="error">{error}</p>
  if (!items) return <p>Завантаження…</p>

  const shown = onlyPending ? items.filter((i) => i.status === 'submitted') : items
  const pending = items.filter((i) => i.status === 'submitted').length
  return (
    <section>
      <h1>Рев'ю</h1>
      <p className="muted">Чекають на рев'ю: {pending} з {items.length}. Рубрики — у приватному репозиторії автора.</p>
      <label className="check"><input type="checkbox" checked={onlyPending} onChange={(e) => setOnlyPending(e.target.checked)} /> Лише без рев'ю</label>
      {shown.length === 0 && <p>Тут порожньо.</p>}
      <div className="list">
        {shown.map((i) => (
          <ReviewCard key={`${i.userId}/${i.caseId}`} item={i}
            onSaved={(a) => setItems((all) => all!.map((x) => (x.userId === i.userId && x.caseId === i.caseId ? { ...x, ...a } : x)))} />
        ))}
      </div>
    </section>
  )
}

function ReviewCard({ item, onSaved }: { item: Item; onSaved: (a: Attempt) => void }) {
  const [open, setOpen] = useState(false)
  const [good, setGood] = useState(item.review?.good ?? '')
  const [fix, setFix] = useState(item.review?.fix ?? '')
  const [next, setNext] = useState(item.review?.next ?? '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function save(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      onSaved(await post<Attempt>(`/review/${item.userId}/${item.caseId}`, { good, fix, next }))
      setOpen(false)
    } catch {
      setError('Не вдалося зберегти. Заповни всі три поля й спробуй ще раз.')
    } finally {
      setBusy(false)
    }
  }

  const s = item.submission!
  return (
    <div className="card review-card">
      <div className="status-row">
        <b>{item.caseTitle}</b>
        <span className={`chip status-${item.status}`}>{STATUS_LABEL[item.status]}</span>
      </div>
      <p className="muted small">{item.email} · здано {formatDate(s.submitted_at)}</p>
      <p><a href={s.link} target="_blank" rel="noreferrer">{s.link}</a></p>
      <p className="pre">{s.conclusion}</p>
      {!open && (
        <button className="btn small" onClick={() => setOpen(true)}>{item.review ? 'Змінити рев’ю' : 'Написати рев’ю'}</button>
      )}
      {open && (
        <form className="form-inline" onSubmit={save}>
          {[['Що добре', good, setGood], ['Що виправити', fix, setFix], ['Що робити далі', next, setNext]].map(([label, value, set]) => (
            <label key={label as string} className="field">
              <span>{label as string}</span>
              <textarea required rows={4} maxLength={4000} value={value as string}
                onChange={(e) => (set as (v: string) => void)(e.target.value)} />
            </label>
          ))}
          {error && <p className="error">{error}</p>}
          <div className="actions">
            <button className="btn" type="submit" disabled={busy}>{busy ? 'Зачекай…' : 'Надіслати рев’ю'}</button>
            <button type="button" className="btn ghost" onClick={() => setOpen(false)}>Скасувати</button>
          </div>
        </form>
      )}
    </div>
  )
}
