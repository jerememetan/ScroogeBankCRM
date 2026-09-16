import { useState } from 'react'
import { INITIAL_ACCOUNTS, INITIAL_AGENTS, INITIAL_CLIENTS } from './data/crm'
import { AppShell } from './components/organisms'
import { AccountsPage, AgentsPage, ClientsPage, DashboardPage, LoginPage, TransactionsPage } from './pages'

export default function App() {
  const [role, setRole] = useState(null)
  const [username, setUsername] = useState('')
  const [screen, setScreen] = useState('login')
  const [clients, setClients] = useState(INITIAL_CLIENTS)
  const [accounts, setAccounts] = useState(INITIAL_ACCOUNTS)
  const [agents, setAgents] = useState(INITIAL_AGENTS)

  function login(nextRole, nextUsername) {
    setRole(nextRole)
    setUsername(nextUsername)
    setScreen(nextRole === 'admin' ? 'admin' : 'agent')
  }

  if (!role) return <LoginPage onLogin={login} />

  return (
    <AppShell
      role={role}
      screen={screen}
      onNavigate={setScreen}
      onLogout={() => {
        setRole(null)
        setUsername('')
        setScreen('login')
      }}
    >
      {screen === 'admin' || screen === 'agent' ? <DashboardPage role={role} username={username} /> : null}
      {screen === 'clients' ? <ClientsPage rows={clients} setRows={setClients} /> : null}
      {screen === 'accounts' ? <AccountsPage rows={accounts} setRows={setAccounts} clients={clients} /> : null}
      {screen === 'agents' ? <AgentsPage rows={agents} setRows={setAgents} /> : null}
      {screen === 'transactions' ? <TransactionsPage /> : null}
    </AppShell>
  )
}
