/**
 * Sign-up / sign-in against the Cognito user pool, with plain fetch calls to the
 * Cognito Identity Provider API (no SDK, so every screen can be in Ukrainian).
 */
import { loadConfig } from './config'

type Tokens = { idToken: string; refreshToken: string; expiresAt: number }
const KEY = 'is.tokens'

async function cognito<T>(action: string, body: object): Promise<T> {
  const { region } = await loadConfig()
  const r = await fetch(`https://cognito-idp.${region}.amazonaws.com/`, {
    method: 'POST',
    headers: {
      'content-type': 'application/x-amz-json-1.1',
      'x-amz-target': `AWSCognitoIdentityProviderService.${action}`,
    },
    body: JSON.stringify(body),
  })
  const data = await r.json()
  if (!r.ok) throw new AuthError(String(data.__type ?? 'Unknown').split('#').pop()!, data.message ?? '')
  return data as T
}

export class AuthError extends Error {
  code: string
  constructor(code: string, message: string) {
    super(message)
    this.code = code
  }
}

const MESSAGES: Record<string, string> = {
  UsernameExistsException: 'Акаунт з цією поштою вже є. Спробуй увійти.',
  NotAuthorizedException: 'Неправильна пошта або пароль.',
  UserNotFoundException: 'Неправильна пошта або пароль.',
  UserNotConfirmedException: 'Пошту ще не підтверджено. Введи код з листа.',
  CodeMismatchException: 'Код не підходить. Перевір лист і спробуй ще раз.',
  ExpiredCodeException: 'Код застарів. Надішли новий.',
  InvalidPasswordException: 'Пароль має містити щонайменше 8 символів і хоча б одну цифру.',
  InvalidParameterException: 'Перевір, чи правильно заповнені поля.',
  LimitExceededException: 'Забагато спроб. Зачекай кілька хвилин.',
  TooManyRequestsException: 'Забагато спроб. Зачекай кілька хвилин.',
}

export function humanError(e: unknown): string {
  if (e instanceof AuthError) return MESSAGES[e.code] ?? 'Щось пішло не так. Спробуй ще раз.'
  return 'Немає зв’язку з сервером. Спробуй ще раз.'
}

export async function signUp(email: string, password: string, name: string) {
  const { clientId } = await loadConfig()
  await cognito('SignUp', {
    ClientId: clientId,
    Username: email,
    Password: password,
    UserAttributes: [{ Name: 'email', Value: email }, ...(name ? [{ Name: 'name', Value: name }] : [])],
  })
}

export async function confirmSignUp(email: string, code: string) {
  const { clientId } = await loadConfig()
  await cognito('ConfirmSignUp', { ClientId: clientId, Username: email, ConfirmationCode: code.trim() })
}

export async function resendCode(email: string) {
  const { clientId } = await loadConfig()
  await cognito('ResendConfirmationCode', { ClientId: clientId, Username: email })
}

type AuthResult = { AuthenticationResult: { IdToken: string; RefreshToken?: string; ExpiresIn: number } }

function store(res: AuthResult, refreshToken?: string) {
  const a = res.AuthenticationResult
  const t: Tokens = {
    idToken: a.IdToken,
    refreshToken: a.RefreshToken ?? refreshToken ?? '',
    expiresAt: Date.now() + (a.ExpiresIn - 60) * 1000,
  }
  localStorage.setItem(KEY, JSON.stringify(t))
  window.dispatchEvent(new Event('auth-changed'))
}

export async function signIn(email: string, password: string) {
  const { clientId } = await loadConfig()
  const res = await cognito<AuthResult>('InitiateAuth', {
    ClientId: clientId,
    AuthFlow: 'USER_PASSWORD_AUTH',
    AuthParameters: { USERNAME: email, PASSWORD: password },
  })
  store(res)
}

export async function forgotPassword(email: string) {
  const { clientId } = await loadConfig()
  await cognito('ForgotPassword', { ClientId: clientId, Username: email })
}

export async function confirmForgotPassword(email: string, code: string, password: string) {
  const { clientId } = await loadConfig()
  await cognito('ConfirmForgotPassword', { ClientId: clientId, Username: email, ConfirmationCode: code.trim(), Password: password })
}

export function signOut() {
  localStorage.removeItem(KEY)
  window.dispatchEvent(new Event('auth-changed'))
}

function read(): Tokens | null {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? 'null')
  } catch {
    return null
  }
}

/** A valid ID token, refreshed if needed; null when signed out. */
export async function getIdToken(): Promise<string | null> {
  const t = read()
  if (!t) return null
  if (Date.now() < t.expiresAt) return t.idToken
  try {
    const { clientId } = await loadConfig()
    const res = await cognito<AuthResult>('InitiateAuth', {
      ClientId: clientId,
      AuthFlow: 'REFRESH_TOKEN_AUTH',
      AuthParameters: { REFRESH_TOKEN: t.refreshToken },
    })
    store(res, t.refreshToken)
    return res.AuthenticationResult.IdToken
  } catch {
    signOut()
    return null
  }
}

export function isSignedIn(): boolean {
  return read() !== null
}

/** Claims from the stored ID token (display only; the API verifies the token itself). */
export function currentClaims(): { email?: string; name?: string } | null {
  const t = read()
  if (!t) return null
  try {
    const part = t.idToken.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const bytes = Uint8Array.from(atob(part), (c) => c.charCodeAt(0))
    return JSON.parse(new TextDecoder().decode(bytes))
  } catch {
    return null
  }
}
