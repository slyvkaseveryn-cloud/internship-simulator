/** Case metadata and files, served as static files from /cases (uploaded by Terraform). */
import { marked } from 'marked'

export type CaseFile = { name: string; caption: string }
export type Case = {
  id: string
  profession: string
  track: string
  level: string
  title: string
  company: string
  teaser: string
  similar: string
  skills: string[]
  tools: string
  time_estimate: string
  deadline_days: number
  sender: string
  first_step: string
  folder: string
  brief: string
  files: CaseFile[]
}
export type Profession = { id: string; emoji: string; title: string; status: 'live' | 'soon'; about?: string }

const cache = new Map<string, Promise<unknown>>()
function getJson<T>(url: string): Promise<T> {
  if (!cache.has(url)) {
    cache.set(url, fetch(url).then((r) => {
      if (!r.ok) throw new Error(url)
      return r.json()
    }))
  }
  return cache.get(url) as Promise<T>
}

export const loadCases = () => getJson<Case[]>('/cases/cases.json')
export const loadProfessions = () => getJson<Profession[]>('/cases/professions.json')

export const fileUrl = (c: Case, name: string) => `/${c.folder}/${encodeURIComponent(name)}`

/** brief.md = the manager's email, then `---`, then the description of the data. Both as HTML. */
export async function loadBrief(c: Case): Promise<{ letter: string; about: string }> {
  const r = await fetch(fileUrl(c, c.brief))
  if (!r.ok) throw new Error('brief')
  const md = await r.text()
  const [letter, ...rest] = md.split(/^---\s*$/m)
  return { letter: await marked.parse(letter), about: await marked.parse(rest.join('---')) }
}

export function daysWord(n: number): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return `${n} день`
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${n} дні`
  return `${n} днів`
}
