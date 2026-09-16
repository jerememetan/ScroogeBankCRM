import { Button } from '../atoms/Button'
import { NavLink } from '../atoms/NavLink'
import { RoleBadge } from '../atoms/RoleBadge'

export function PrimaryNav({ items, current, onNavigate }) {
  return (
    <nav aria-label="Primary">
      {items.map(([id, label]) => (
        <NavLink
          key={id}
          href={`#${id}`}
          current={current === id}
          onClick={(event) => {
            event.preventDefault()
            onNavigate(id)
          }}
        >
          {label}
        </NavLink>
      ))}
    </nav>
  )
}

export function SessionBar({ role, onLogout }) {
  return (
    <div className="session">
      <RoleBadge>{role === 'admin' ? 'Admin' : 'Agent'}</RoleBadge>
      <Button variant="inverse" onClick={onLogout}>Log out</Button>
    </div>
  )
}
