import { cx } from '../../utils/cx'

export function Select({ className, onChange, ...props }) {
  const filled = Boolean(props.value ?? props.defaultValue)
  return (
    <select
      className={cx('control', className)}
      data-filled={filled ? '' : undefined}
      onChange={(event) => {
        event.currentTarget.toggleAttribute('data-filled', Boolean(event.currentTarget.value))
        onChange?.(event)
      }}
      {...props}
    />
  )
}
