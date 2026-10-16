import { useEffect, useState } from 'react'
import type { ImportTask } from '../../hooks/useImportTasks'
import styles from './FileTaskCard.module.css'

interface Props {
  task: ImportTask
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return seconds.toFixed(1) + 's'
  const mins = Math.floor(seconds / 60)
  const secs = (seconds % 60).toFixed(0)
  return `${mins}m${secs}s`
}

function statusLabel(status: ImportTask['status']): string {
  switch (status) {
    case 'uploading':
      return '上传中'
    case 'processing':
      return '处理中'
    case 'completed':
      return '已完成'
    case 'error':
      return '失败'
  }
}

function barColor(percent: number, status: ImportTask['status']): string {
  if (status === 'completed' || percent >= 100) return 'linear-gradient(90deg, #10b981, #059669)'
  if (percent < 10) return 'linear-gradient(90deg, #f59e0b, #fbbf24)'
  return 'linear-gradient(90deg, #1f6feb, #148a78)'
}

export function FileTaskCard({ task }: Props) {
  const [open, setOpen] = useState(true)

  useEffect(() => {
    if (task.status === 'completed') {
      const t = window.setTimeout(() => setOpen(false), 1000)
      return () => window.clearTimeout(t)
    }
  }, [task.status])

  let totalDuration = 0
  for (const v of Object.values(task.durations)) totalDuration += v
  const totalText = totalDuration > 0 ? ` · 总耗时 ${formatDuration(totalDuration)}` : ''

  const summary = `运行日志 · 已完成 ${task.doneList.length} · 进行中 ${task.runningList.length} · 共 ${task.totalNodes} 步${totalText}`

  return (
    <div className={styles.card}>
      <div className={styles.info}>
        <div className={styles.header}>
          <span className={styles.name}>{task.fileName}</span>
          <span className={styles.size}>{(task.fileSize / 1024).toFixed(2)} KB</span>
        </div>

        <div className={styles.progress}>
          <div className={styles.track}>
            <div
              className={styles.bar}
              style={{
                width: `${Math.min(Math.max(task.percent, 0), 100)}%`,
                background: barColor(task.percent, task.status),
              }}
            />
          </div>
          <div className={styles.pct}>{Math.round(task.percent)}%</div>
        </div>

        <details
          className={styles.logs}
          open={open}
          onToggle={(e) => setOpen((e.currentTarget as HTMLDetailsElement).open)}
        >
          <summary>{task.status === 'uploading' ? '准备上传...' : summary}</summary>
          <ul className={styles.list}>
            {task.doneList
              .filter((item) => item !== 'upload_file')
              .map((item) => (
                <li key={`d-${item}`} className={styles.done}>
                  <span>{item} 节点执行完成</span>
                  {task.durations[item] !== undefined && (
                    <span className={styles.duration}>{formatDuration(task.durations[item])}</span>
                  )}
                </li>
              ))}
            {task.runningList.map((item) => (
              <li key={`r-${item}`} className={styles.running}>
                {item.startsWith('开始') ? item : `正在处理 ${item} 节点...`}
              </li>
            ))}
            {task.error && <li className={styles.err}>{task.error}</li>}
          </ul>
        </details>
      </div>
      <div className={`${styles.badge} ${styles[task.status]}`}>{statusLabel(task.status)}</div>
    </div>
  )
}
