import type { Session } from './types';

export async function fetchSessions(signal?: AbortSignal): Promise<Session[]> {
  const response = await fetch('/api/sessions', { signal });
  if (!response.ok) throw new Error('Session history is unavailable. Restart the Python backend to load the updated session service.');
  const result = await response.json();
  if (!Array.isArray(result)) throw new Error('The session service returned an unexpected response.');
  return result;
}

export function sessionDate(value: string | null): string {
  if (!value || Number.isNaN(Date.parse(value))) return 'Date unavailable';
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
}

export function sessionDuration(value: number): string {
  return `${(value / 1000).toFixed(1)}s`;
}

export function sessionDownload(file: string): string {
  return `/api/sessions/${encodeURIComponent(file)}`;
}
