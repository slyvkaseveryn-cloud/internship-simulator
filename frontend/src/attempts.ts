export type Review = { good: string; fix: string; next: string; reviewed_at: string }
export type Attempt = {
  caseId: string
  takenAt: string
  deadline: string
  status: 'taken' | 'submitted' | 'reviewed'
  submission: { link: string; conclusion: string; submitted_at: string } | null
  review: Review | null
}

export const STATUS_LABEL: Record<Attempt['status'], string> = {
  taken: 'Взято',
  submitted: 'Здано, чекає на рев’ю',
  reviewed: 'Рев’ю отримано',
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('uk-UA', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
}
