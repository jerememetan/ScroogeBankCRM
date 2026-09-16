import { cx } from '../../utils/cx'

function markFilled(event, onInput) {
  event.currentTarget.toggleAttribute('data-filled', Boolean(event.currentTarget.value))
  onInput?.(event)
}

export function TextInput({ className, placeholder = ' ', onInput, onClick, type, ...props }) {
  const filled = Boolean(props.value ?? props.defaultValue)
  return (
    <input
      className={cx('control', className)}
      type={type}
      placeholder={placeholder}
      data-filled={filled ? '' : undefined}
      onInput={(event) => markFilled(event, onInput)}
      onClick={(event) => {
        if (type === 'date' && typeof event.currentTarget.showPicker === 'function') {
          try {
            event.currentTarget.showPicker()
          } catch {
            /* Picker unavailable, native typing still works. */
          }
        }
        onClick?.(event)
      }}
      {...props}
    />
  )
}
