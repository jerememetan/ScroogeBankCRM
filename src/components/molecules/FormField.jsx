import { Select } from '../atoms/Select'
import { TextInput } from '../atoms/TextInput'

export function FormField({ label, children }) {
  return (
    <label className="field">
      {children}
      <span className="field-label">{label}</span>
    </label>
  )
}

export function FieldControl({ field }) {
  if (field.type === 'select') {
    return (
      <FormField label={field.label}>
        <Select name={field.name} defaultValue={field.defaultValue ?? ''}>
          {field.placeholder ? <option value="" disabled hidden></option> : null}
          {field.options.map((option) => <option key={option}>{option}</option>)}
        </Select>
      </FormField>
    )
  }

  return (
    <FormField label={field.label}>
      <TextInput
        type={field.type}
        name={field.name}
        defaultValue={field.defaultValue}
        autoComplete={field.autoComplete}
      />
    </FormField>
  )
}
