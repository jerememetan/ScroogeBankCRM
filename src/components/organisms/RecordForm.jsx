import { Button } from '../atoms/Button'
import { Heading } from '../atoms/Heading'
import { ButtonRow, FieldControl, FormGrid } from '../molecules'

export function RecordForm({ title, fields, onSave, onCancel, submitLabel = 'Save' }) {
  return (
    <FormGrid wide onSubmit={onSave}>
      {title ? <Heading level={2} className="span-all">{title}</Heading> : null}
      {fields.map((field) => <FieldControl key={field.name} field={field} />)}
      <ButtonRow className="span-all">
        <Button type="submit">{submitLabel}</Button>
        <Button variant="secondary" onClick={onCancel}>Cancel</Button>
      </ButtonRow>
    </FormGrid>
  )
}
