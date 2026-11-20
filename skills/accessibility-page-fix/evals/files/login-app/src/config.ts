export interface AppConfig {
  apiUrl: string;
  /** The "Please sign in again" dialog opens when the session has this many seconds left. */
  sessionWarningSeconds: number;
}

let config: AppConfig | undefined;

/** Runtime configuration, loaded once at start-up from /config.json (each environment deploys its own). */
export async function loadConfig(): Promise<AppConfig> {
  const response = await fetch('/config.json');
  config = (await response.json()) as AppConfig;
  return config;
}

export function getConfig(): AppConfig {
  if (!config) throw new Error('Config not loaded');
  return config;
}
