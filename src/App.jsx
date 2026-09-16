import { useState } from 'react'
import { AppShell } from './components/organisms'
import { AccountsPage, ClientProfilePage, DashboardPage, LoginPage, TransactionsPage } from './pages'

export default function App() {
  const [role, setRole] = useState(null)
  const [username, setUsername] = useState('')
  const [screen, setScreen] = useState('login')

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
      {screen === 'accounts' ? <AccountsPage /> : null}
      {screen === 'client' ? <ClientProfilePage onCancel={() => setScreen('agent')} /> : null}
      {screen === 'transactions' ? <TransactionsPage /> : null}
    </AppShell>
  )
}
