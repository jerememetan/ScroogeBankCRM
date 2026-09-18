import { useState } from 'react'
import { INITIAL_TRANSACTIONS } from '../../data/crm'
import { useListFilter } from '../../hooks/useListFilter'
import { Button } from '../atoms/Button'
import { StatusBadge } from '../atoms/StatusBadge'
import { DataTable, SearchToolbar, TableActions } from '../molecules'
import { Section } from './AppShell'

function transactionValues(row) {
  return [row.id, row.amount, row.type, row.status, row.date]
}

export function TransactionManager({ account, onBack }) {
  const [rows, setRows] = useState(() => INITIAL_TRANSACTIONS.filter((row) => row.accountId === account.id))
  const [selected, setSelected] = useState(null)
  const { query, setQuery, visible, applySearch } = useListFilter(rows, transactionValues)
  const selectedStatus = rows.find((row) => row.id === selected?.id)?.status || selected?.status

  return (
    <>
      <SearchToolbar
        label="Transaction controls"
        query={query}
        onQueryChange={(event) => setQuery(event.target.value)}
        placeholder="Date, type, or amount"
        onSearch={applySearch}
      >
        <Button variant="secondary" onClick={onBack}>Back to accounts</Button>
      </SearchToolbar>
      <Section title={`Transactions for ${account.client}`} titleId="transaction-list">
        <DataTable
          caption={`Transactions for ${account.client}`}
          empty="No transactions for this account yet."
          rows={visible}
          columns={[
            { key: 'date', header: 'Date' },
            { key: 'id', header: 'Transaction ID' },
            { key: 'type', header: 'Type' },
            { key: 'amount', header: 'Amount' },
            { key: 'status', header: 'Status', render: (row) => <StatusBadge value={row.status} /> },
            { key: 'actions', header: 'Actions', render: (row) => (
              <TableActions>
                <Button variant="ghost" onClick={() => setSelected(row)}>View Details</Button>
                {row.status !== 'Completed' ? (
                  <Button className="py-5" variant="ghost" onClick={() => setRows((current) => current.map((item) => item.id === row.id ? { ...item, status: 'Completed' } : item))}>Retry</Button>
                ) : null}
              </TableActions>
            ) },
          ]}
        />
      </Section>
      {selected ? (
        <Section title={`Transaction ${selected.id}`} aria-label="Transaction details">
          <p>{selected.type} of {selected.amount} on {selected.date} for {account.client} ({account.id}, {account.type}).</p>
          <p>Status: <StatusBadge value={selectedStatus} /></p>
          <Button variant="secondary" onClick={() => setSelected(null)}>Close</Button>
        </Section>
      ) : null}
    </>
  )
}
