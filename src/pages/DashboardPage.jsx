import { formatUserName } from '../data/crm'
import { Heading } from '../components/atoms/Heading'
import { ActivityList } from '../components/organisms'

export function DashboardPage({ role, username }) {
  return (
    <div className="dashboard">
      <ActivityList role={role} />
      <section className="dashboard-main" aria-labelledby="dashboard-welcome">
        <Heading id="dashboard-welcome">Welcome back, {formatUserName(username)}</Heading>
      </section>
    </div>
  )
}
