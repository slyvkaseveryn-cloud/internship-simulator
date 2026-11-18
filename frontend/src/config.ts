export type AppConfig = { region: string; userPoolId: string; clientId: string; donateUrl?: string }

let cached: Promise<AppConfig> | null = null

/** Runtime config written by Terraform to /config.json (no rebuild when infra changes). */
export function loadConfig(): Promise<AppConfig> {
  cached ??= fetch('/config.json', { cache: 'no-cache' }).then((r) => {
    if (!r.ok) throw new Error('config.json not found')
    return r.json()
  })
  return cached
}
