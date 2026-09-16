import { AccountManager } from '../components/organisms'

export function AccountsPage({ rows, setRows, clients }) {
  return <AccountManager rows={rows} setRows={setRows} clients={clients} />
}
