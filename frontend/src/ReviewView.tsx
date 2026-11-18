import type { Review } from './attempts'
import { formatDate } from './attempts'

/** The team-lead review as the student sees it. */
export default function ReviewView({ review }: { review: Review }) {
  return (
    <div className="review">
      <h3>Рев'ю</h3>
      <p className="muted small">{formatDate(review.reviewed_at)}</p>
      <h4>Що добре</h4>
      <p className="pre">{review.good}</p>
      <h4>Що виправити</h4>
      <p className="pre">{review.fix}</p>
      <h4>Що робити далі</h4>
      <p className="pre">{review.next}</p>
    </div>
  )
}
