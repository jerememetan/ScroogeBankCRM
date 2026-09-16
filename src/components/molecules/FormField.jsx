import { Select } from '../atoms/Select'
import { TextInput } from '../atoms/TextInput'

export function FormField({ label, children }) {
  return <label className="field">{label}{children}</label>
}

export function FieldControl({ field }) {
  if (field.type === 'select') {
    return (
      <FormField label={field.label}>
        <Select name={field.name} defaultValue={field.defaultValue ?? ''}>
          {field.placeholder ? <option value="" disabled>{field.placeholder}</option> : null}
          {field.options.map((option) => <option key={option}>{option}</option>)}
        </Select>
      </FormField>
    )
  }

  return (
    <FormField label={field.label}>
      <TextInput type={field.type} name={field.name} defaultValue={field.defaultValue} autoComplete={field.autoComplete} />
    </FormField>
  )
}
