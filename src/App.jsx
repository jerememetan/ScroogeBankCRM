import { useState } from 'react'
import { AppShell } from './components/organisms'
import { AccountsPage, ClientProfilePage, DashboardPage, LoginPage, TransactionsPage } from './pages'

export default function App() {
  const [role, setRole] = useState(null)
  const [screen, setScreen] = useState('login')

  function login(nextRole) {
    setRole(nextRole)
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
        setScreen('login')
      }}
    >
      {screen === 'admin' || screen === 'agent' ? <DashboardPage role={role} /> : null}
      {screen === 'accounts' ? <AccountsPage /> : null}
      {screen === 'client' ? <ClientProfilePage onCancel={() => setScreen('agent')} /> : null}
      {screen === 'transactions' ? <TransactionsPage /> : null}
    </AppShell>
  )
}
