import { useEffect, useState } from 'react'
import { api } from '../api'

type Me = { email: string; isReviewer: boolean }

export default function Account() {
  const [me, setMe] = useState<Me | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api<Me>('/me').then(setMe).catch(() => setError('Не вдалося завантажити профіль. Онови сторінку.'))
  }, [])

  return (
    <section className="card">
      <h1>Кабінет</h1>
      {error && <p className="error">{error}</p>}
      {me && (
        <>
          <p>Ти увійшов як <b>{me.email}</b>{me.isReviewer && ' (рецензент)'}.</p>
          <p className="note">Кейси з'являться тут найближчим часом.</p>
        </>
      )}
      {!me && !error && <p>Завантаження…</p>}
    </section>
  )
}
