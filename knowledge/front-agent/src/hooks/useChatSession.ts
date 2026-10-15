import { useCallback, useEffect, useRef, useState } from 'react'
import { clearHistory, fetchHistory, openStream, submitQuery } from '../api/query'
import { mapNodeToTool } from '../lib/toolMap'
import {
  createSession,
  ensureActiveSession,
  loadSessions,
  removeSession,
  setActiveSessionId,
  touchSession,
} from '../lib/sessionStore'
import type { ChatMessage, ProgressPayload, SessionMeta, ToolCall } from '../types'

function msgId(): string {
  return 'm-' + Math.random().toString(36).slice(2) + Date.now().toString(36)
}

function toolsFromProgress(data: ProgressPayload): ToolCall[] {
  const done = Array.isArray(data.done_list) ? data.done_list : []
  const running = Array.isArray(data.running_list) ? data.running_list : []
  const tools: ToolCall[] = []
  const seen = new Set<string>()

  for (const name of done) {
    const mapped = mapNodeToTool(name)
    const key = mapped.id + ':done:' + name
    if (seen.has(mapped.id)) continue
    seen.add(mapped.id)
    tools.push({
      id: key,
      name: mapped.id,
      displayName: mapped.label,
      status: 'done',
    })
  }
  for (const name of running) {
    const mapped = mapNodeToTool(name)
    if (seen.has(mapped.id)) continue
    seen.add(mapped.id)
    tools.push({
      id: mapped.id + ':run:' + name,
      name: mapped.id,
      displayName: mapped.label,
      status: 'running',
    })
  }
  return tools
}

function markAllToolsDone(tools: ToolCall[] | undefined): ToolCall[] {
  return (tools || []).map((t) => ({ ...t, status: 'done' as const }))
}

export function useChatSession() {
  const boot = ensureActiveSession()
  const [sessions, setSessions] = useState<SessionMeta[]>(boot.sessions)
  const [sessionId, setSessionId] = useState(boot.activeId)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [sending, setSending] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const esRef = useRef<EventSource | null>(null)
  const rawAnswerRef = useRef('')

  const refreshSessions = useCallback(() => {
    setSessions(loadSessions())
  }, [])

  const loadSessionHistory = useCallback(async (id: string) => {
    setLoadingHistory(true)
    try {
      const items = await fetchHistory(id)
      const mapped: ChatMessage[] = items.map((item) => ({
        id: msgId(),
        role: item.role === 'user' ? 'user' : 'assistant',
        text: item.text || '',
        imageUrls: item.image_urls || [],
        status: 'done',
        ts: item.ts,
      }))
      setMessages(mapped)
    } catch {
      setMessages([])
    } finally {
      setLoadingHistory(false)
    }
  }, [])

  useEffect(() => {
    void loadSessionHistory(sessionId)
    return () => {
      esRef.current?.close()
    }
  }, [sessionId, loadSessionHistory])

  const switchSession = useCallback(
    (id: string) => {
      esRef.current?.close()
      setActiveSessionId(id)
      setSessionId(id)
      refreshSessions()
    },
    [refreshSessions],
  )

  const newSession = useCallback(() => {
    esRef.current?.close()
    const s = createSession()
    setSessionId(s.id)
    setMessages([])
    refreshSessions()
  }, [refreshSessions])

  const clearCurrent = useCallback(async () => {
    if (!confirm('确定要清空当前会话的历史记录吗？这将无法恢复。')) return
    esRef.current?.close()
    try {
      await clearHistory(sessionId)
    } catch {
      /* local clear anyway */
    }
    setMessages([])
  }, [sessionId])

  const deleteSession = useCallback(
    (id: string) => {
      esRef.current?.close()
      const next = removeSession(id)
      setSessionId(next)
      refreshSessions()
    },
    [refreshSessions],
  )

  const send = useCallback(
    async (text: string) => {
      const query = text.trim()
      if (!query || sending) return

      setSending(true)
      rawAnswerRef.current = ''

      const userMsg: ChatMessage = {
        id: msgId(),
        role: 'user',
        text: query,
        status: 'done',
        ts: Date.now() / 1000,
      }
      const botId = msgId()
      const botMsg: ChatMessage = {
        id: botId,
        role: 'assistant',
        text: '',
        tools: [],
        status: 'streaming',
        ts: Date.now() / 1000,
      }

      setMessages((prev) => [...prev, userMsg, botMsg])
      touchSession(sessionId, query)
      refreshSessions()

      try {
        const data = await submitQuery(query, sessionId)
        const taskId = data.task_id
        if (!taskId) throw new Error('未返回 task_id')

        esRef.current?.close()
        esRef.current = openStream(taskId, {
          onProgress: (p) => {
            const tools = toolsFromProgress(p)
            setMessages((prev) =>
              prev.map((m) => (m.id === botId ? { ...m, tools } : m)),
            )
            if (p.status === 'completed') {
              setSending(false)
            }
          },
          onDelta: (delta) => {
            rawAnswerRef.current += delta
            const snapshot = rawAnswerRef.current
            setMessages((prev) =>
              prev.map((m) => (m.id === botId ? { ...m, text: snapshot } : m)),
            )
          },
          onFinal: (final) => {
            const finalText =
              typeof final.answer === 'string' && final.answer.trim().length > 0
                ? final.answer
                : rawAnswerRef.current
            setMessages((prev) =>
              prev.map((m) =>
                m.id === botId
                  ? {
                      ...m,
                      text: final.error
                        ? `抱歉，本次处理失败：\n${final.error}`
                        : finalText,
                      imageUrls: final.image_urls || [],
                      tools: markAllToolsDone(m.tools),
                      status: final.error ? 'error' : 'done',
                    }
                  : m,
              ),
            )
            setSending(false)
          },
          onError: (message) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === botId
                  ? {
                      ...m,
                      text: (rawAnswerRef.current || m.text) + `\n\n（错误：${message}）`,
                      tools: markAllToolsDone(m.tools),
                      status: 'error',
                    }
                  : m,
              ),
            )
            setSending(false)
          },
        })
      } catch (e) {
        const err = e instanceof Error ? e.message : String(e)
        setMessages((prev) =>
          prev.map((m) =>
            m.id === botId
              ? { ...m, text: `请求失败：${err}`, status: 'error' }
              : m,
          ),
        )
        setSending(false)
      }
    },
    [sending, sessionId, refreshSessions],
  )

  return {
    sessions,
    sessionId,
    messages,
    sending,
    loadingHistory,
    send,
    switchSession,
    newSession,
    clearCurrent,
    deleteSession,
  }
}
