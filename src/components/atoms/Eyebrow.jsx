import { cx } from '../../utils/cx'

export function Eyebrow({ inverse = false, children }) {
  return <p className={cx('eyebrow', inverse && 'eyebrow--inverse')}>{children}</p>
}
