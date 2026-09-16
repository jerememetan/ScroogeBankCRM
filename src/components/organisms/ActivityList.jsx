import { ACTIVITIES } from '../../data/crm'
import { Section } from './AppShell'

export function ActivityList({ role }) {
  const items = ACTIVITIES[role]
  const title = role === 'admin' ? 'Recent Activities' : 'My Recent Activities'

  return (
    <Section title={title} titleId="recent-activity">
      <ul>
        {items.map((activity) => <li key={activity}>{activity}</li>)}
      </ul>
    </Section>
  )
}
