export type ToolStatus = 'running' | 'done'

export interface ToolCall {
  id: string
  name: string
  displayName: string
  status: ToolStatus
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  imageUrls?: string[]
  tools?: ToolCall[]
  status?: 'streaming' | 'done' | 'error'
  ts?: number
}

export interface SessionMeta {
  id: string
  title: string
  updatedAt: number
}

export interface HistoryItem {
  role: 'user' | 'assistant' | string
  text?: string
  ts?: number
  image_urls?: string[]
}

export interface ProgressPayload {
  done_list?: string[]
  running_list?: string[]
  status?: string
}

export interface DeltaPayload {
  delta?: string
}

export interface FinalPayload {
  answer?: string
  error?: string
  image_urls?: string[]
}
