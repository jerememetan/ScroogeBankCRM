import { useState } from 'react'
import { ACCOUNT_STATUSES, ACCOUNT_TYPES } from '../../data/crm'
import { useListFilter } from '../../hooks/useListFilter'
import { hasMissingFields, nextId, personName, readFields, withDefaults } from '../../utils/records'
import { Button } from '../atoms/Button'
import { StatusBadge } from '../atoms/StatusBadge'
import { DataTable, SearchToolbar, TableActions } from '../molecules'
import { Section } from './AppShell'
import { RecordForm } from './RecordForm'

function accountValues(row) {
  return [row.id, row.client, row.type, row.status]
}

function accountFields(clients) {
  const names = clients.map(personName)
  return [
    {
      label: 'Client',
      name: 'client',
      type: 'select',
      options: names,
      placeholder: names.length ? 'Select client' : 'Add a client first',
    },
    { label: 'Type', name: 'type', type: 'select', options: ACCOUNT_TYPES, defaultValue: 'Savings' },
    { label: 'Status', name: 'status', type: 'select', options: ACCOUNT_STATUSES, defaultValue: 'Active' },
  ]
}

export function AccountManager({ rows, setRows, clients }) {
  const [editor, setEditor] = useState(null)
  const { query, setQuery, visible, applySearch } = useListFilter(rows, accountValues)
  const fields = accountFields(clients)

  function save(event) {
    event.preventDefault()
    const values = readFields(event.currentTarget, fields)
    if (hasMissingFields(values, fields)) return
    setRows((current) => editor?.id
      ? current.map((row) => (row.id === editor.id ? { ...row, ...values } : row))
      : [...current, { ...values, id: nextId('A', current) }])
    setEditor(null)
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
        <Button variant="secondary" onClick={() => setEditor({})}>Add Account</Button>
      </SearchToolbar>
      {editor ? (
        <RecordForm
          key={editor.id ?? 'new-account'}
          title={editor.id ? 'Edit Account' : 'New Account'}
          fields={withDefaults(fields, editor.id ? editor : undefined)}
          onSave={save}
          onCancel={() => setEditor(null)}
        />
      ) : null}
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
              <TableActions>
                <Button variant="ghost" onClick={() => setEditor(row)}>Edit</Button>
                <Button variant="ghost" tone="danger" onClick={() => setRows((current) => current.filter((item) => item.id !== row.id))}>Delete</Button>
              </TableActions>
            ) },
          ]}
        />
      </Section>
    </>
  )
}
