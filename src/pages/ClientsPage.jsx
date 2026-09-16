import { ClientManager } from '../components/organisms'

export function ClientsPage({ rows, setRows }) {
  return <ClientManager rows={rows} setRows={setRows} />
}
