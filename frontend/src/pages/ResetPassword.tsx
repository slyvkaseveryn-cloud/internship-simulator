import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { confirmForgotPassword, forgotPassword, humanError } from '../auth'
import { Field, Form } from './Form'

export default function ResetPassword() {
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [password, setPassword] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (!sent) {
        await forgotPassword(email.trim())
        setSent(true)
      } else {
        await confirmForgotPassword(email.trim(), code, password)
        nav(`/signin?email=${encodeURIComponent(email.trim())}`)
      }
    } catch (err) {
      setError(humanError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Form title="Новий пароль" onSubmit={submit} error={error} busy={busy} submit={sent ? 'Змінити пароль' : 'Надіслати код'}>
      <Field label="Пошта" type="email" value={email} onChange={setEmail} autoComplete="email" />
      {sent && (
        <>
          <Field label="Код з листа" value={code} onChange={setCode} autoComplete="one-time-code" />
          <Field label="Новий пароль" type="password" value={password} onChange={setPassword} autoComplete="new-password"
            hint="Щонайменше 8 символів і хоча б одна цифра" />
        </>
      )}
    </Form>
  )
}
