import type { QueryMode } from '../api/query'

const KEY = 'wenqi_query_mode'

export function loadQueryMode(): QueryMode {
  try {
    const v = localStorage.getItem(KEY)
    return v === 'agent' ? 'agent' : 'dag'
  } catch {
    return 'dag'
  }
}

export function saveQueryMode(mode: QueryMode): void {
  localStorage.setItem(KEY, mode)
}
