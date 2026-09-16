import { useState } from 'react'
import { ACCOUNT_TYPES, CLIENT_FIELDS } from '../../data/crm'
import { Button } from '../atoms/Button'
import { Heading } from '../atoms/Heading'
import { Message } from '../atoms/Message'
import { ButtonRow, FieldControl, FormGrid } from '../molecules'

export function ClientForm({ onCancel }) {
  const [message, setMessage] = useState('')

  function save(event) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const missing = CLIENT_FIELDS.some((field) => !String(data.get(field.name) || '').trim())
    setMessage(missing ? 'Fill in every field before saving.' : 'Client profile saved.')
  }

  return (
    <FormGrid wide onSubmit={save}>
      {message ? (
        <Message className="span-all" tone={message.includes('saved') ? 'success' : 'danger'} role="status">
          {message}
        </Message>
      ) : null}
      {CLIENT_FIELDS.map((field) => <FieldControl key={field.name} field={field} />)}
      <ButtonRow className="span-all">
        <Button type="submit">Save</Button>
        <Button variant="secondary" onClick={onCancel}>Cancel</Button>
      </ButtonRow>
    </FormGrid>
  )
}

const ACCOUNT_FIELDS = [
  { label: 'Client', name: 'client', type: 'text' },
  { label: 'Type', name: 'type', type: 'select', options: ACCOUNT_TYPES, defaultValue: 'Savings' },
]

export function AccountForm({ onSave, onCancel }) {
  return (
    <FormGrid wide onSubmit={onSave}>
      <Heading level={2} className="span-all">New Account</Heading>
      {ACCOUNT_FIELDS.map((field) => <FieldControl key={field.name} field={field} />)}
      <ButtonRow className="span-all">
        <Button type="submit">Save Account</Button>
        <Button variant="secondary" onClick={onCancel}>Cancel</Button>
      </ButtonRow>
    </FormGrid>
  )
}
