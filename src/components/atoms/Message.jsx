import { cx } from '../../utils/cx'

export function Message({ tone = 'muted', className, children, ...props }) {
  return <p className={cx('message', `message--${tone}`, className)} {...props}>{children}</p>
}
