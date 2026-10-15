import { useEffect, useRef, useState } from 'react'
import type { QueryMode } from '../api/query'
import styles from './Composer.module.css'

interface Props {
  disabled?: boolean
  seed?: string
  queryMode: QueryMode
  onQueryModeChange: (mode: QueryMode) => void
  onSend: (text: string) => void
}

export function Composer({ disabled, seed, queryMode, onQueryModeChange, onSend }: Props) {
  const [value, setValue] = useState('')
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (seed) {
      setValue(seed)
      ref.current?.focus()
    }
  }, [seed])

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }, [value])

  const submit = () => {
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.shell}>
        <div className={styles.chips}>
          <span className={styles.chip}>知识库</span>
          <span className={styles.chip}>联网</span>
          <button
            type="button"
            className={`${styles.modeChip} ${queryMode === 'dag' ? styles.modeActive : ''}`}
            disabled={disabled}
            onClick={() => onQueryModeChange('dag')}
            title="固定 LangGraph RAG 流水线"
          >
            DAG
          </button>
          <button
            type="button"
            className={`${styles.modeChip} ${queryMode === 'agent' ? styles.modeActive : ''}`}
            disabled={disabled}
            onClick={() => onQueryModeChange('agent')}
            title="openai-agents 编排（学习轨）"
          >
            Agent
          </button>
        </div>
        <div className={styles.row}>
          <textarea
            ref={ref}
            className={styles.input}
            placeholder={
              queryMode === 'agent'
                ? 'Agent 轨：由模型决定调哪些工具…'
                : '有问题尽管问，Shift+Enter 换行'
            }
            value={value}
            disabled={disabled}
            rows={1}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                submit()
              }
            }}
          />
          <button type="button" className={styles.send} disabled={disabled || !value.trim()} onClick={submit}>
            发送
          </button>
        </div>
      </div>
      <div className={styles.hint}>
        当前：{queryMode === 'agent' ? 'Agent 编排' : 'DAG 流水线'} ·{' '}
        <span className={styles.kbd}>Enter</span> 发送 · <span className={styles.kbd}>Shift</span>+
        <span className={styles.kbd}>Enter</span> 换行
      </div>
    </div>
  )
}
