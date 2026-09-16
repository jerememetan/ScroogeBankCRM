import { useState } from 'react'
import { CLIENT_FIELDS } from '../../data/crm'
import { useListFilter } from '../../hooks/useListFilter'
import { hasMissingFields, nextId, personName, readFields, withDefaults } from '../../utils/records'
import { Button } from '../atoms/Button'
import { DataTable, SearchToolbar, TableActions } from '../molecules'
import { Section } from './AppShell'
import { RecordForm } from './RecordForm'

function clientValues(row) {
  return [row.id, personName(row), row.email, row.phone]
}

export function ClientManager({ rows, setRows }) {
  const [editor, setEditor] = useState(null)
  const { query, setQuery, visible, applySearch } = useListFilter(rows, clientValues)

  function save(event) {
    event.preventDefault()
    const values = readFields(event.currentTarget, CLIENT_FIELDS)
    if (hasMissingFields(values, CLIENT_FIELDS)) return
    setRows((current) => editor?.id
      ? current.map((row) => (row.id === editor.id ? { ...row, ...values } : row))
      : [...current, { ...values, id: nextId('C', current) }])
    setEditor(null)
  }

  return (
    <>
      <SearchToolbar
        label="Client controls"
        query={query}
        onQueryChange={(event) => setQuery(event.target.value)}
        placeholder="Client name, ID, or email"
        onSearch={applySearch}
      >
        <Button variant="secondary" onClick={() => setEditor({})}>Add Client</Button>
      </SearchToolbar>
      {editor ? (
        <RecordForm
          key={editor.id ?? 'new-client'}
          title={editor.id ? 'Edit Client' : 'New Client'}
          fields={withDefaults(CLIENT_FIELDS, editor.id ? editor : undefined)}
          onSave={save}
          onCancel={() => setEditor(null)}
        />
      ) : null}
      <Section title="Client List" titleId="client-list">
        <DataTable
          caption="Client List"
          empty="No clients match that search."
          rows={visible}
          columns={[
            { key: 'id', header: 'Client ID' },
            { key: 'name', header: 'Name', render: (row) => personName(row) },
            { key: 'email', header: 'Email' },
            { key: 'phone', header: 'Phone' },
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
