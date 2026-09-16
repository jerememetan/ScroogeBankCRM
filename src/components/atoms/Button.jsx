import { cx } from '../../utils/cx'

export function Button({ variant = 'primary', tone, type = 'button', className, ...props }) {
  return <button type={type} className={cx('button', `button--${variant}`, tone && `button--${tone}`, className)} {...props} />
}
