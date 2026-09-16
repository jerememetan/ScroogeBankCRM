import { cx } from '../../utils/cx'

export function Heading({ level = 1, className, children, ...props }) {
  const Tag = `h${level}`
  return <Tag className={cx('heading', `heading--${level}`, className)} {...props}>{children}</Tag>
}
