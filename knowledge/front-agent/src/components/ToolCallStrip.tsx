import { useEffect, useState } from 'react'
import type { ToolCall } from '../types'
import styles from './ToolCallStrip.module.css'

interface Props {
  tools: ToolCall[]
  defaultOpen?: boolean
}

export function ToolCallStrip({ tools, defaultOpen = true }: Props) {
  const running = tools.some((t) => t.status === 'running')
  const done = tools.filter((t) => t.status === 'done').length
  const [open, setOpen] = useState(defaultOpen || running)

  useEffect(() => {
    if (running) setOpen(true)
  }, [running])

  if (!tools.length) return null

  return (
    <details
      className={styles.strip}
      open={open}
      onToggle={(e) => setOpen((e.currentTarget as HTMLDetailsElement).open)}
    >
      <summary className={styles.summary}>
        <span className={`${styles.dot} ${running ? styles.dotRunning : ''}`} />
        思考过程 · {done}/{tools.length}
        {running ? ' · 进行中' : ''}
      </summary>
      <ul className={styles.list}>
        {tools.map((t) => (
          <li key={t.id} className={styles.row}>
            <span className={styles.badge}>{t.name}</span>
            <span className={styles.label}>{t.displayName}</span>
            <span className={styles.status}>{t.status === 'running' ? '运行中' : '完成'}</span>
          </li>
        ))}
      </ul>
    </details>
  )
}
