import { ACTIVITIES } from '../../data/crm'
import { Heading } from '../atoms/Heading'

export function ActivityList({ role }) {
  const items = ACTIVITIES[role]
  const title = role === 'admin' ? 'Recent Activities' : 'My Recent Activities'

  return (
    <aside className="surface activity-rail" aria-labelledby="recent-activity">
      <Heading level={2} id="recent-activity">{title}</Heading>
      <ul>
        {items.map((activity) => <li key={activity}>{activity}</li>)}
      </ul>
    </aside>
  )
}
