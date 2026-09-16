import { cx } from '../../utils/cx'

export function ButtonRow({ className, children }) {
  return <div className={cx('cluster', className)}>{children}</div>
}
