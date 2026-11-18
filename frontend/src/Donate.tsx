import { useEffect, useState } from 'react'
import { track } from './api'
import { loadConfig } from './config'

/**
 * «Підтримати волонтерів»: a link to a known charity fund's collection (config.json → donateUrl).
 * We never take money ourselves. A click is our "paying with money" signal (event donate_clicked).
 */
export default function Donate({ caseId }: { caseId?: string }) {
  const [url, setUrl] = useState<string | null>(null)
  const [stubNote, setStubNote] = useState(false)

  useEffect(() => {
    loadConfig().then((c) => setUrl(c.donateUrl ?? '')).catch(() => setUrl(''))
  }, [])

  if (url === null) return null
  return (
    <div className="card donate">
      <b>Рев'ю безкоштовне.</b>
      <p>Якщо воно тобі допомогло, підтримай волонтерів: будь-яка сума йде напряму у збір благодійного фонду, не нам.</p>
      {url ? (
        <a className="btn" href={url} target="_blank" rel="noreferrer" onClick={() => track('donate_clicked', caseId)}>
          Підтримати волонтерів
        </a>
      ) : (
        <button className="btn" onClick={() => { track('donate_clicked', caseId, 'stub'); setStubNote(true) }}>
          Підтримати волонтерів
        </button>
      )}
      {stubNote && <p className="muted small">Посилання на збір з'явиться тут найближчим часом. Дякуємо!</p>}
    </div>
  )
}
