import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchImportStatus, uploadFile } from '../api/importApi'

export type TaskStatus = 'uploading' | 'processing' | 'completed' | 'error'

export interface ImportTask {
  id: string
  fileName: string
  fileSize: number
  totalNodes: number
  status: TaskStatus
  percent: number
  doneList: string[]
  runningList: string[]
  durations: Record<string, number>
  error?: string
  taskId?: string
}

function uid(): string {
  return 'file-' + Math.random().toString(36).slice(2, 10)
}

function calcPercent(
  doneLen: number,
  runningLen: number,
  totalNodes: number,
): number {
  let pct = (doneLen / totalNodes) * 100
  if (runningLen > 0) pct += (0.5 / totalNodes) * 100
  if (pct >= 100) pct = 95
  return pct
}

export function useImportTasks() {
  const [tasks, setTasks] = useState<ImportTask[]>([])
  const timers = useRef<Map<string, number>>(new Map())

  useEffect(() => {
    return () => {
      for (const t of timers.current.values()) window.clearInterval(t)
      timers.current.clear()
    }
  }, [])

  const updateTask = useCallback((id: string, patch: Partial<ImportTask>) => {
    setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, ...patch } : t)))
  }, [])

  const startPoll = useCallback(
    (localId: string, taskId: string, totalNodes: number) => {
      const prev = timers.current.get(localId)
      if (prev) window.clearInterval(prev)

      const interval = window.setInterval(async () => {
        try {
          const data = await fetchImportStatus(taskId)
          const done = Array.isArray(data.done_list) ? data.done_list : []
          const running = Array.isArray(data.running_list) ? data.running_list : []
          const durations = data.durations || {}

          if (data.status === 'completed') {
            window.clearInterval(interval)
            timers.current.delete(localId)
            updateTask(localId, {
              status: 'completed',
              percent: 100,
              doneList: done,
              runningList: [],
              durations,
            })
            return
          }

          if (data.status === 'failed') {
            window.clearInterval(interval)
            timers.current.delete(localId)
            updateTask(localId, {
              status: 'error',
              doneList: done,
              runningList: running,
              durations,
              error: data.error || '工作流执行失败中止',
            })
            return
          }

          updateTask(localId, {
            status: 'processing',
            percent: calcPercent(done.length, running.length, totalNodes),
            doneList: done,
            runningList: running,
            durations,
          })
        } catch (e) {
          console.error('Polling error', e)
        }
      }, 1500)

      timers.current.set(localId, interval)
    },
    [updateTask],
  )

  const enqueueFiles = useCallback(
    async (files: FileList | File[]) => {
      const list = Array.from(files).filter((f) => {
        const n = f.name.toLowerCase()
        return n.endsWith('.pdf') || n.endsWith('.md')
      })

      for (const file of list) {
        const isPDF = file.name.toLowerCase().endsWith('.pdf')
        const totalNodes = isPDF ? 8 : 7
        const id = uid()

        setTasks((prev) => [
          {
            id,
            fileName: file.name,
            fileSize: file.size,
            totalNodes,
            status: 'uploading',
            percent: Math.min((1 / totalNodes) * 100, 10),
            doneList: [],
            runningList: ['开始上传文件...'],
            durations: {},
          },
          ...prev,
        ])

        try {
          const result = await uploadFile(file)
          const uploadPct = (1 / totalNodes) * 100
          updateTask(id, {
            status: 'processing',
            percent: uploadPct,
            taskId: result.task_id,
            runningList: [],
          })
          startPoll(id, result.task_id, totalNodes)
        } catch (e) {
          updateTask(id, {
            status: 'error',
            percent: 0,
            runningList: [],
            error: e instanceof Error ? e.message : '网络请求失败或服务器异常',
          })
        }
      }
    },
    [startPoll, updateTask],
  )

  return { tasks, enqueueFiles }
}
