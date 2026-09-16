import { useState } from 'react'
import { INITIAL_TRANSACTIONS } from '../../data/crm'
import { useListFilter } from '../../hooks/useListFilter'
import { Button } from '../atoms/Button'
import { StatusBadge } from '../atoms/StatusBadge'
import { DataTable, SearchToolbar } from '../molecules'
import { Section } from './AppShell'

function transactionValues(row) {
  return [row.id, row.amount, row.type, row.status, row.clientId]
}

export function TransactionManager() {
  const [rows, setRows] = useState(INITIAL_TRANSACTIONS)
  const [selected, setSelected] = useState(null)
  const { query, setQuery, visible, applySearch } = useListFilter(rows, transactionValues)
  const selectedStatus = rows.find((row) => row.id === selected?.id)?.status || selected?.status

  return (
    <>
      <SearchToolbar
        label="Transaction controls"
        query={query}
        onQueryChange={(event) => setQuery(event.target.value)}
        placeholder="Transaction or client ID"
        onSearch={applySearch}
      />
      <Section title="Transaction List" titleId="transaction-list">
        <DataTable
          empty="No transactions match that search."
          rows={visible}
          columns={[
            { key: 'id', header: 'Transaction ID' },
            { key: 'amount', header: 'Amount' },
            { key: 'type', header: 'Type' },
            { key: 'status', header: 'Status', render: (row) => <StatusBadge value={row.status} /> },
            { key: 'actions', header: 'Actions', render: (row) => (
              <>
                <Button variant="ghost" onClick={() => setSelected(row)}>View Details</Button>
                {row.status !== 'Completed' ? (
                  <Button variant="ghost" onClick={() => setRows((current) => current.map((item) => item.id === row.id ? { ...item, status: 'Completed' } : item))}>Retry</Button>
                ) : null}
              </>
            ) },
          ]}
        />
      </Section>
      {selected ? (
        <Section title={`Transaction ${selected.id}`} aria-label="Transaction details">
          <p>{selected.type} of {selected.amount} on {selected.date} for client {selected.clientId}.</p>
          <p>Status: <StatusBadge value={selectedStatus} /></p>
          <Button variant="secondary" onClick={() => setSelected(null)}>Close</Button>
        </Section>
      ) : null}
    </>
  )
}
