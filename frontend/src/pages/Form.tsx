import type { FormEvent, ReactNode } from 'react'

export function Form(props: { title: string; onSubmit: (e: FormEvent) => void; error?: string; busy?: boolean; submit: string; children: ReactNode; footer?: ReactNode }) {
  return (
    <form className="card form" onSubmit={props.onSubmit}>
      <h1>{props.title}</h1>
      {props.children}
      {props.error && <p className="error" role="alert">{props.error}</p>}
      <button className="btn" type="submit" disabled={props.busy}>{props.busy ? 'Зачекай…' : props.submit}</button>
      {props.footer && <div className="footer">{props.footer}</div>}
    </form>
  )
}

export function Field(props: { label: string; type?: string; value: string; onChange: (v: string) => void; autoComplete?: string; required?: boolean; hint?: string }) {
  return (
    <label className="field">
      <span>{props.label}</span>
      <input type={props.type ?? 'text'} value={props.value} required={props.required ?? true} autoComplete={props.autoComplete}
        onChange={(e) => props.onChange(e.target.value)} />
      {props.hint && <small>{props.hint}</small>}
    </label>
  )
}
