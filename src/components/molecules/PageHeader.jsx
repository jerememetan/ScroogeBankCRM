import { Eyebrow } from '../atoms/Eyebrow'
import { Heading } from '../atoms/Heading'

export function PageHeader({ kicker, title }) {
  return (
    <header className="page-header">
      {kicker ? <Eyebrow>{kicker}</Eyebrow> : null}
      <Heading>{title}</Heading>
    </header>
  )
}
