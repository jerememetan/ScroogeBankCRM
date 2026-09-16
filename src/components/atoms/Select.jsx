import { cx } from '../../utils/cx'

export function Select({ className, children, ...props }) {
  return <select className={cx('control', className)} {...props}>{children}</select>
}
