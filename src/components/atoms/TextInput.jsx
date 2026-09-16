import { cx } from '../../utils/cx'

export function TextInput({ className, ...props }) {
  return <input className={cx('control', className)} {...props} />
}
