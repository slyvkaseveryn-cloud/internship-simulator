import { anonId } from './anon'

/** "Opened the site": once per browser session, before any sign-in (top of the funnel). */
export function trackOpened() {
  try {
    if (sessionStorage.getItem('is.opened')) return
    sessionStorage.setItem('is.opened', '1')
  } catch {
    /* storage blocked: still count this load */
  }
  fetch('/api/public/events', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-anon-id': anonId() },
    body: JSON.stringify({ event: 'opened' }),
    keepalive: true,
  }).catch(() => {})
}
