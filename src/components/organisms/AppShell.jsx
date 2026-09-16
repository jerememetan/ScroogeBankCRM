import { NAV, PAGE_TITLES } from '../../data/crm'
import { cx } from '../../utils/cx'
import { Heading } from '../atoms/Heading'
import { BrandMark, PageHeader, PrimaryNav, SessionBar } from '../molecules'

export function AppShell({ role, screen, onNavigate, onLogout, children }) {
  const dashboard = screen === 'admin' || screen === 'agent'

  return (
    <div className="app">
      <header className="shell">
        <BrandMark inverse />
        <PrimaryNav items={NAV[role]} current={screen} onNavigate={onNavigate} />
        <SessionBar role={role} onLogout={onLogout} />
      </header>
      <main className={cx('page', dashboard && 'page--dashboard')}>
        {dashboard ? null : <PageHeader title={PAGE_TITLES[screen]} />}
        {children}
      </main>
    </div>
  )
}

export function PublicLayout({ kicker, title, children }) {
  return (
    <main className="page">
      <PageHeader kicker={kicker} title={title} />
      {children}
    </main>
  )
}

export function Section({ title, titleId, children, ...props }) {
  return (
    <section className="surface" aria-labelledby={titleId} {...props}>
      {title ? <Heading level={2} id={titleId}>{title}</Heading> : null}
      {children}
    </section>
  )
}
