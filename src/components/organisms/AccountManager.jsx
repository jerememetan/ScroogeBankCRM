import { useState } from 'react'
import { INITIAL_ACCOUNTS } from '../../data/crm'
import { useListFilter } from '../../hooks/useListFilter'
import { Button } from '../atoms/Button'
import { StatusBadge } from '../atoms/StatusBadge'
import { DataTable, SearchToolbar } from '../molecules'
import { AccountForm } from './ClientForm'
import { Section } from './AppShell'

function accountValues(row) {
  return [row.id, row.client, row.type, row.status]
}

export function AccountManager() {
  const [rows, setRows] = useState(INITIAL_ACCOUNTS)
  const [draft, setDraft] = useState(false)
  const { query, setQuery, visible, applySearch } = useListFilter(rows, accountValues)

  function addAccount(event) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const client = String(data.get('client') || '').trim()
    if (!client) return
    setRows((current) => [
      ...current,
      { id: String(9100 + current.length + 2), client, type: String(data.get('type') || 'Savings'), status: 'Pending' },
    ])
    event.currentTarget.reset()
    setDraft(false)
  }

  return (
    <>
      <SearchToolbar
        label="Account controls"
        query={query}
        onQueryChange={(event) => setQuery(event.target.value)}
        placeholder="Account ID or client name"
        onSearch={applySearch}
      >
        <Button variant="secondary" onClick={() => setDraft(true)}>Add New Account</Button>
      </SearchToolbar>
      {draft ? <AccountForm onSave={addAccount} onCancel={() => setDraft(false)} /> : null}
      <Section title="Account List" titleId="account-list">
        <DataTable
          caption="Account List"
          empty="No accounts match that search."
          rows={visible}
          columns={[
            { key: 'id', header: 'Account ID' },
            { key: 'client', header: 'Client' },
            { key: 'type', header: 'Type' },
            { key: 'status', header: 'Status', render: (row) => <StatusBadge value={row.status} /> },
            { key: 'actions', header: 'Actions', render: (row) => (
              <Button variant="ghost" tone="danger" onClick={() => setRows((current) => current.filter((item) => item.id !== row.id))}>Delete</Button>
            ) },
          ]}
        />
      </Section>
    </>
  )
}
