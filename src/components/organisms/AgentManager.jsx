import { useState } from 'react'
import { AGENT_FIELDS } from '../../data/crm'
import { useListFilter } from '../../hooks/useListFilter'
import { hasMissingFields, nextId, personName, readFields, withDefaults } from '../../utils/records'
import { Button } from '../atoms/Button'
import { StatusBadge } from '../atoms/StatusBadge'
import { DataTable, SearchToolbar, TableActions } from '../molecules'
import { Section } from './AppShell'
import { RecordForm } from './RecordForm'

function agentValues(row) {
  return [row.id, personName(row), row.email, row.role, row.status]
}

function toggleStatus(row) {
  return { ...row, status: row.status === 'Disabled' ? 'Active' : 'Disabled' }
}

export function AgentManager({ rows, setRows }) {
  const [editor, setEditor] = useState(null)
  const { query, setQuery, visible, applySearch } = useListFilter(rows, agentValues)

  function save(event) {
    event.preventDefault()
    const values = readFields(event.currentTarget, AGENT_FIELDS)
    if (hasMissingFields(values, AGENT_FIELDS)) return
    setRows((current) => editor?.id
      ? current.map((row) => (row.id === editor.id ? { ...row, ...values } : row))
      : [...current, { ...values, id: nextId('U', current), status: 'Active' }])
    setEditor(null)
  }

  return (
    <>
      <SearchToolbar
        label="Agent controls"
        query={query}
        onQueryChange={(event) => setQuery(event.target.value)}
        placeholder="Agent name, email, or role"
        onSearch={applySearch}
      >
        <Button variant="secondary" onClick={() => setEditor({})}>Add Agent</Button>
      </SearchToolbar>
      {editor ? (
        <RecordForm
          key={editor.id ?? 'new-agent'}
          title={editor.id ? 'Edit Agent' : 'New Agent'}
          fields={withDefaults(AGENT_FIELDS, editor.id ? editor : undefined)}
          onSave={save}
          onCancel={() => setEditor(null)}
        />
      ) : null}
      <Section title="Agent List" titleId="agent-list">
        <DataTable
          caption="Agent List"
          empty="No agents match that search."
          rows={visible}
          columns={[
            { key: 'id', header: 'Staff ID' },
            { key: 'name', header: 'Name', render: (row) => personName(row) },
            { key: 'email', header: 'Email' },
            { key: 'role', header: 'Role' },
            { key: 'status', header: 'Status', render: (row) => <StatusBadge value={row.status} /> },
            { key: 'actions', header: 'Actions', render: (row) => (
              <TableActions>
                <Button variant="ghost" onClick={() => setEditor(row)}>Edit</Button>
                {row.protected ? null : (
                  <>
                    <Button variant="ghost" onClick={() => setRows((current) => current.map((item) => item.id === row.id ? toggleStatus(item) : item))}>
                      {row.status === 'Disabled' ? 'Enable' : 'Disable'}
                    </Button>
                    <Button variant="ghost" tone="danger" onClick={() => setRows((current) => current.filter((item) => item.id !== row.id))}>Delete</Button>
                  </>
                )}
              </TableActions>
            ) },
          ]}
        />
      </Section>
    </>
  )
}
