import { cx } from '../../utils/cx'

export function FormGrid({ wide = false, className, children, ...props }) {
  return <form className={cx('surface', 'form', wide && 'form--wide', className)} {...props}>{children}</form>
}
