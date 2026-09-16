import { cleanup, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import App from './App'

afterEach(cleanup)

async function loginAs(user, role = 'agent') {
  await user.type(screen.getByLabelText('Username'), 'jdoe')
  await user.type(screen.getByLabelText('Password'), 'password')
  await user.click(screen.getByRole('button', { name: role === 'admin' ? 'Login as Admin' : 'Login' }))
}

describe('CRM wireframe', () => {
  it('opens the agent dashboard after login', async () => {
    const user = userEvent.setup()
    render(<App />)

    await loginAs(user)

    expect(screen.getByRole('heading', { name: 'Welcome back, Jdoe' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'My Recent Activities' })).toBeInTheDocument()
    expect(screen.getByText('Scrooge Global Bank')).toBeInTheDocument()
    expect(screen.getByText('Agent')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Log out' })).toBeInTheDocument()
  })

  it('opens the client profile form from the agent dashboard', async () => {
    const user = userEvent.setup()
    render(<App />)

    await loginAs(user)
    await user.click(screen.getByRole('link', { name: 'Create Client' }))

    expect(screen.getByRole('heading', { name: 'Create Client Profile' })).toBeInTheDocument()
    expect(screen.getByLabelText('Postal Code')).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Gender' })).toBeInTheDocument()
  })

  it('rejects empty login credentials', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: 'Login' }))

    expect(screen.getByRole('alert')).toHaveTextContent('Enter a username and password.')
    expect(screen.queryByRole('heading', { name: 'Welcome back, Jdoe' })).not.toBeInTheDocument()
  })

  it('returns to login after logout', async () => {
    const user = userEvent.setup()
    render(<App />)

    await loginAs(user)
    await user.click(screen.getByRole('button', { name: 'Log out' }))

    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('opens the admin dashboard and returns there from transactions', async () => {
    const user = userEvent.setup()
    render(<App />)

    await loginAs(user, 'admin')

    expect(screen.getByRole('heading', { name: 'Welcome back, Jdoe' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Recent Activities' })).toBeInTheDocument()
    expect(screen.getByText('Admin')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Settings' })).not.toBeInTheDocument()

    await user.click(screen.getByRole('link', { name: 'Transactions' }))
    expect(screen.getByRole('heading', { name: 'View Transactions' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Welcome back, Jdoe' })).not.toBeInTheDocument()

    await user.click(screen.getByRole('link', { name: 'Dashboard' }))
    expect(screen.getByRole('heading', { name: 'Welcome back, Jdoe' })).toBeInTheDocument()
  })

  it('filters the account list from search', async () => {
    const user = userEvent.setup()
    render(<App />)

    await loginAs(user, 'admin')
    await user.click(screen.getByRole('link', { name: 'Accounts' }))
    await user.type(screen.getByLabelText('Search'), 'Jane')
    await user.click(screen.getByRole('button', { name: 'Search' }))

    const table = screen.getByRole('table', { name: 'Account List' })
    expect(within(table).getByText('Jane Smith')).toBeInTheDocument()
    expect(within(table).queryByText('John Doe')).not.toBeInTheDocument()
  })
})
