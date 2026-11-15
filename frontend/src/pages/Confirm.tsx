import { useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { confirmSignUp, humanError, resendCode } from '../auth'
import { Field, Form } from './Form'

export default function Confirm() {
  const [params] = useSearchParams()
  const [email, setEmail] = useState(params.get('email') ?? '')
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await confirmSignUp(email.trim(), code)
      nav(`/signin?email=${encodeURIComponent(email.trim())}&confirmed=1`)
    } catch (err) {
      setError(humanError(err))
    } finally {
      setBusy(false)
    }
  }

  async function resend() {
    setError('')
    try {
      await resendCode(email.trim())
      setNote('Новий код надіслано.')
    } catch (err) {
      setError(humanError(err))
    }
  }

  return (
    <Form title="Підтверди пошту" onSubmit={submit} error={error} busy={busy} submit="Підтвердити"
      footer={<>Лист не прийшов? Перевір «Спам» або <button type="button" className="link" onClick={resend}>надішли код ще раз</button>.</>}>
      <p>Ми надіслали 6-значний код на пошту.</p>
      <Field label="Пошта" type="email" value={email} onChange={setEmail} autoComplete="email" />
      <Field label="Код з листа" value={code} onChange={setCode} autoComplete="one-time-code" />
      {note && <p className="note">{note}</p>}
    </Form>
  )
}
