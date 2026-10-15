import type { FinalPayload, HistoryItem, ProgressPayload } from '../types'

const API_BASE = ''

export interface StreamHandlers {
  onProgress: (data: ProgressPayload) => void
  onDelta: (delta: string) => void
  onFinal: (data: FinalPayload) => void
  onError: (message: string) => void
}

export async function submitQuery(
  query: string,
  sessionId: string,
): Promise<{ task_id: string; session_id?: string }> {
  const res = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      session_id: sessionId,
      is_stream: true,
    }),
  })
  if (!res.ok) {
    const msg = await res.text()
    throw new Error(msg || '请求失败')
  }
  return res.json()
}

export function openStream(taskId: string, handlers: StreamHandlers): EventSource {
  const es = new EventSource(`${API_BASE}/stream/${taskId}`)

  es.addEventListener('progress', (e) => {
    try {
      const d = JSON.parse((e as MessageEvent).data || '{}') as ProgressPayload
      handlers.onProgress(d)
    } catch {
      /* ignore */
    }
  })

  es.addEventListener('delta', (e) => {
    try {
      const d = JSON.parse((e as MessageEvent).data || '{}') as { delta?: string }
      if (d.delta) handlers.onDelta(d.delta)
    } catch {
      /* ignore */
    }
  })

  const handleFinal = (e: Event) => {
    try {
      const d = JSON.parse((e as MessageEvent).data || '{}') as FinalPayload
      handlers.onFinal(d)
    } catch {
      handlers.onFinal({})
    }
    es.close()
  }

  es.addEventListener('final', handleFinal)
  es.addEventListener('final_answer', handleFinal)

  es.addEventListener('error', () => {
    handlers.onError('SSE 连接中断/失败')
    es.close()
  })

  return es
}

export async function fetchHistory(sessionId: string): Promise<HistoryItem[]> {
  const res = await fetch(`${API_BASE}/history/${sessionId}`)
  if (!res.ok) return []
  const data = await res.json()
  return Array.isArray(data.items) ? data.items : []
}

export async function clearHistory(sessionId: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/history/${sessionId}`, { method: 'DELETE' })
  return res.ok
}
