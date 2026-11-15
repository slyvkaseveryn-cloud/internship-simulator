import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { AuthError, humanError, signIn } from '../auth'
import { Field, Form } from './Form'

export default function SignIn() {
  const [params] = useSearchParams()
  const [email, setEmail] = useState(params.get('email') ?? '')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await signIn(email.trim(), password)
      nav('/account')
    } catch (err) {
      if (err instanceof AuthError && err.code === 'UserNotConfirmedException') {
        nav(`/confirm?email=${encodeURIComponent(email.trim())}`)
        return
      }
      setError(humanError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Form title="Вхід" onSubmit={submit} error={error} busy={busy} submit="Увійти"
      footer={<><Link to="/reset">Забув пароль?</Link> · Немає акаунта? <Link to="/signup">Зареєструватись</Link></>}>
      {params.get('confirmed') && <p className="note">Пошту підтверджено. Тепер увійди.</p>}
      <Field label="Пошта" type="email" value={email} onChange={setEmail} autoComplete="email" />
      <Field label="Пароль" type="password" value={password} onChange={setPassword} autoComplete="current-password" />
    </Form>
  )
}
