import { cx } from '../../utils/cx'

export function Image({ className, alt, ...props }) {
  return <img className={cx('media', className)} alt={alt} {...props} />
}
