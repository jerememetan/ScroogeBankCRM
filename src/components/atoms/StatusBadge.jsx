import { cx } from '../../utils/cx'

const TONE = {
  Active: 'success',
  Completed: 'success',
  Pending: 'warning',
  Failed: 'danger',
}

export function StatusBadge({ value }) {
  return <span className={cx('badge', `badge--${TONE[value] || 'success'}`)}>{value}</span>
}
