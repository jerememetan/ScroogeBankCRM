import loginBackground from '../assets/login-background.png'
import { Heading } from '../components/atoms/Heading'
import { BrandMark } from '../components/molecules'
import { LoginForm } from '../components/organisms'

export function LoginPage({ onLogin }) {
  return (
    <div
      className="login-screen"
      style={{ '--image-login': `url(${loginBackground})` }}
    >
      <section className="login-panel">
        <BrandMark className="login-lockup" />
        <Heading>Sign in</Heading>
        <LoginForm onLogin={onLogin} />
      </section>
      <div className="login-visual" role="img" aria-label="Scrooge Global Bank lobby" />
    </div>
  )
}
