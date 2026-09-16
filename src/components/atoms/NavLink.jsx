export function NavLink({ current, children, ...props }) {
  return <a className="nav-link" aria-current={current ? 'page' : undefined} {...props}>{children}</a>
}
