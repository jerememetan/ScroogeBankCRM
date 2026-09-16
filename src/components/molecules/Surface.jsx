import { cx } from '../../utils/cx'

export function Surface({ as: Tag = 'section', className, children, ...props }) {
  return <Tag className={cx('surface', className)} {...props}>{children}</Tag>
}
