import { parseAnswerAndImages } from '../lib/answerParse'
import type { ChatMessage } from '../types'
import { ToolCallStrip } from './ToolCallStrip'
import styles from './MessageBubble.module.css'

interface Props {
  message: ChatMessage
}

function formatTime(ts?: number): string {
  const d = ts ? new Date(Number(ts) * 1000) : new Date()
  if (Number.isNaN(d.getTime())) {
    return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'
  const { text, images } = isUser
    ? { text: message.text, images: [] as string[] }
    : parseAnswerAndImages(message.text, message.imageUrls || [])

  const showTyping =
    !isUser && message.status === 'streaming' && !text.trim() && !(message.tools?.length)

  return (
    <div className={`${styles.row} ${isUser ? styles.rowUser : ''}`}>
      <div className={`${styles.avatar} ${!isUser ? styles.avatarBot : ''}`}>
        {isUser ? '我' : '问器'}
      </div>
      <div className={styles.body}>
        <div className={styles.bubble}>
          {!isUser && message.tools && message.tools.length > 0 && (
            <ToolCallStrip
              tools={message.tools}
              defaultOpen={message.status === 'streaming'}
            />
          )}
          {showTyping ? (
            <span className={styles.typing} aria-label="正在思考">
              <span />
              <span />
              <span />
            </span>
          ) : (
            <>
              {text.trim() ? <div>{text}</div> : null}
              {images.length > 0 && (
                <div className={styles.images}>
                  {images.map((url) => (
                    <div key={url}>
                      <img
                        src={url}
                        alt="参考图片"
                        loading="lazy"
                        referrerPolicy="no-referrer"
                        onError={(e) => {
                          ;(e.currentTarget as HTMLImageElement).style.display = 'none'
                        }}
                      />
                      <a href={url} target="_blank" rel="noopener noreferrer">
                        {url}
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
        <div className={styles.meta}>{formatTime(message.ts)}</div>
      </div>
    </div>
  )
}
