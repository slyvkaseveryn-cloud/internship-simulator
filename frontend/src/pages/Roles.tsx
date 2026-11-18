import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { put } from '../api'
import { loadCases, loadProfessions, type Case, type Profession } from '../cases'
import { useMe } from '../useMe'

const casesWord = (n: number) => `${n} ${n % 10 === 1 && n % 100 !== 11 ? 'кейс' : [2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100) ? 'кейси' : 'кейсів'}`

export default function Roles() {
  const [profs, setProfs] = useState<Profession[]>([])
  const [cases, setCases] = useState<Case[]>([])
  const [error, setError] = useState('')
  const { me, setMe } = useMe()
  const nav = useNavigate()

  useEffect(() => {
    Promise.all([loadProfessions(), loadCases()]).then(([p, c]) => {
      setProfs(p)
      setCases(c)
    }).catch(() => setError('Не вдалося завантажити напрями. Онови сторінку.'))
  }, [])

  async function choose(p: Profession) {
    if (me?.profession !== p.id) {
      try {
        const r = await put<{ profession: string }>('/me/profession', { profession: p.id })
        if (me) setMe({ ...me, profession: r.profession })
      } catch {
        /* the list still opens; the choice is saved next time */
      }
    }
    nav(`/roles/${p.id}`)
  }

  const live = profs.filter((p) => p.status === 'live')
  const soon = profs.filter((p) => p.status === 'soon')

  return (
    <section>
      <h1>Обери напрям</h1>
      <p className="muted">Кейси зроблені як тестові завдання на junior-позицію в цьому напрямі.</p>
      {error && <p className="error">{error}</p>}
      <div className="grid">
        {live.map((p) => (
          <button key={p.id} className={`card role ${me?.profession === p.id ? 'current' : ''}`} onClick={() => choose(p)}>
            <span className="emoji" aria-hidden>{p.emoji}</span>
            <b>{p.title}</b>
            <span className="muted">{p.about}</span>
            <span className="chip">{casesWord(cases.filter((c) => c.profession === p.id).length)}</span>
          </button>
        ))}
      </div>
      {soon.length > 0 && (
        <>
          <h2>Незабаром</h2>
          <div className="grid">
            {soon.map((p) => (
              <div key={p.id} className="card role soon" aria-disabled>
                <span className="emoji" aria-hidden>{p.emoji}</span>
                <b>{p.title}</b>
                <span className="chip">незабаром</span>
              </div>
            ))}
          </div>
        </>
      )}
      <p className="muted small"><Link to="/">Як це працює</Link></p>
    </section>
  )
}
