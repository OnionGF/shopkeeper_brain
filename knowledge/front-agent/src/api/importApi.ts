export interface ImportStatusPayload {
  status: string
  done_list?: string[]
  running_list?: string[]
  durations?: Record<string, number>
  error?: string
}

/** 与问答同源；统一入口后开发/生产都走同一 API_BASE */
function apiBase(): string {
  return (import.meta.env.VITE_API_BASE as string | undefined) || ''
}

export async function uploadFile(file: File): Promise<{ task_id: string; message?: string }> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${apiBase()}/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const msg = await res.text()
    throw new Error(msg || 'Upload failed')
  }
  return res.json()
}

export async function fetchImportStatus(taskId: string): Promise<ImportStatusPayload> {
  const res = await fetch(`${apiBase()}/status/${taskId}`)
  if (!res.ok) throw new Error('Status request failed')
  return res.json()
}
