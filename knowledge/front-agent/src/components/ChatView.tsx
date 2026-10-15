import { useEffect, useRef } from 'react'
import type { ChatMessage } from '../types'
import { MessageBubble } from './MessageBubble'
import styles from './ChatView.module.css'

interface Props {
  messages: ChatMessage[]
  onHint: (text: string) => void
}

const HINTS = [
  '如何使用万用表测量电压？',
  '这款产品怎么接线？',
  '有没有尺寸图可以参考？',
]

export function ChatView({ messages, onHint }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const empty = messages.length === 0

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages])

  return (
    <div className={styles.main}>
      <div className={styles.scroll}>
        {empty ? (
          <div className={styles.welcome}>
            <h1 className={styles.heroBrand}>Agent Brain</h1>
            <p className={styles.heroLead}>
              多工具协同的知识库问答。检索、联网、重排都会以工具调用的形式呈现。
            </p>
            <div className={styles.hints}>
              {HINTS.map((h) => (
                <button key={h} type="button" className={styles.hint} onClick={() => onHint(h)}>
                  {h}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className={styles.stream}>
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
