import { useState } from 'react'
import { Button } from '../atoms/Button'
import { Message } from '../atoms/Message'
import { ButtonRow, FieldControl, FormGrid } from '../molecules'

const LOGIN_FIELDS = [
  { label: 'Username', name: 'username', type: 'text', autoComplete: 'username' },
  { label: 'Password', name: 'password', type: 'password', autoComplete: 'current-password' },
]

export function LoginForm({ onLogin }) {
  const [error, setError] = useState('')

  function submit(role) {
    return (event) => {
      event.preventDefault()
      const form = event.currentTarget.closest('form')
      const data = new FormData(form)
      if (!String(data.get('username') || '').trim() || !String(data.get('password') || '')) {
        setError('Enter a username and password.')
        return
      }
      onLogin(role)
    }
  }

  return (
    <FormGrid onSubmit={submit('agent')}>
      {error ? <Message tone="danger" role="alert">{error}</Message> : null}
      {LOGIN_FIELDS.map((field) => <FieldControl key={field.name} field={field} />)}
      <ButtonRow>
        <Button type="submit">Login</Button>
        <Button variant="secondary" onClick={submit('admin')}>Login as Admin</Button>
      </ButtonRow>
    </FormGrid>
  )
}
