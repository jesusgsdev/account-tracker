/**
 * Parse a datetime string from the API as UTC.
 * The API now returns ISO strings with a trailing 'Z'; older/naive strings
 * (no timezone designator) are treated as UTC too.
 */
export function parseApiDate(s: string): Date {
  const iso = s.includes(' ') ? s.replace(' ', 'T') : s
  const hasTz = /(Z|[+-]\d{2}:?\d{2})$/i.test(iso)
  return new Date(hasTz ? iso : iso + 'Z')
}

/** Format an API datetime as a relative age, e.g. "just now", "5 min ago", "3 h ago", "2 d ago". */
export function timeAgo(s: string | null | undefined, now: Date = new Date()): string {
  if (!s) return 'unknown'
  const t = parseApiDate(s).getTime()
  if (Number.isNaN(t)) return 'unknown'
  const mins = Math.floor((now.getTime() - t) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins} min ago`
  const hours = Math.floor(mins / 60)
  if (hours < 48) return `${hours} h ago`
  return `${Math.floor(hours / 24)} d ago`
}
