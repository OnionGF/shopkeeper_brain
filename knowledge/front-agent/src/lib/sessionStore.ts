import type { SessionMeta } from '../types'

const SESSIONS_KEY = 'wenqi_agent_sessions'
const ACTIVE_KEY = 'wenqi_agent_active_session'

function uid(): string {
  return 'sess-' + Math.random().toString(36).slice(2) + Date.now().toString(36)
}

export function loadSessions(): SessionMeta[] {
  try {
    const raw = localStorage.getItem(SESSIONS_KEY)
    if (!raw) return []
    const list = JSON.parse(raw) as SessionMeta[]
    return Array.isArray(list) ? list : []
  } catch {
    return []
  }
}

export function saveSessions(sessions: SessionMeta[]): void {
  localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions))
}

export function getActiveSessionId(): string | null {
  return localStorage.getItem(ACTIVE_KEY)
}

export function setActiveSessionId(id: string): void {
  localStorage.setItem(ACTIVE_KEY, id)
}

export function ensureActiveSession(): { sessions: SessionMeta[]; activeId: string } {
  let sessions = loadSessions()
  let activeId = getActiveSessionId()

  if (!activeId || !sessions.some((s) => s.id === activeId)) {
    if (sessions.length === 0) {
      const id = uid()
      sessions = [{ id, title: '新会话', updatedAt: Date.now() }]
      saveSessions(sessions)
      activeId = id
    } else {
      activeId = sessions[0].id
    }
    setActiveSessionId(activeId)
  }

  return { sessions, activeId }
}

export function createSession(title = '新会话'): SessionMeta {
  const session: SessionMeta = { id: uid(), title, updatedAt: Date.now() }
  const sessions = [session, ...loadSessions()]
  saveSessions(sessions)
  setActiveSessionId(session.id)
  return session
}

export function touchSession(id: string, title?: string): void {
  const sessions = loadSessions().map((s) => {
    if (s.id !== id) return s
    return {
      ...s,
      title: title && s.title === '新会话' ? title.slice(0, 28) : s.title,
      updatedAt: Date.now(),
    }
  })
  sessions.sort((a, b) => b.updatedAt - a.updatedAt)
  saveSessions(sessions)
}

export function removeSession(id: string): string {
  let sessions = loadSessions().filter((s) => s.id !== id)
  if (sessions.length === 0) {
    const next = createSession()
    return next.id
  }
  saveSessions(sessions)
  const active = getActiveSessionId()
  if (active === id) {
    setActiveSessionId(sessions[0].id)
    return sessions[0].id
  }
  return active || sessions[0].id
}
