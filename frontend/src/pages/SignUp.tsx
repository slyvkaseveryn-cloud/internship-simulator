import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { humanError, signUp } from '../auth'
import { Field, Form } from './Form'

export default function SignUp() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await signUp(email.trim(), password, name.trim())
      nav(`/confirm?email=${encodeURIComponent(email.trim())}`)
    } catch (err) {
      setError(humanError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Form title="Реєстрація" onSubmit={submit} error={error} busy={busy} submit="Зареєструватись"
      footer={<>Вже є акаунт? <Link to="/signin">Увійти</Link></>}>
      <Field label="Ім'я" value={name} onChange={setName} autoComplete="name" required={false} />
      <Field label="Пошта" type="email" value={email} onChange={setEmail} autoComplete="email" />
      <Field label="Пароль" type="password" value={password} onChange={setPassword} autoComplete="new-password"
        hint="Щонайменше 8 символів і хоча б одна цифра" />
    </Form>
  )
}
