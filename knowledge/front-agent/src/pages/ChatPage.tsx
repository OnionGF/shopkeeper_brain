import { useState } from 'react'
import { ChatView } from '../components/ChatView'
import { Composer } from '../components/Composer'
import { Sidebar } from '../components/Sidebar'
import { useChatSession } from '../hooks/useChatSession'
import styles from '../App.module.css'

export function ChatPage() {
  const {
    sessions,
    sessionId,
    messages,
    sending,
    queryMode,
    setQueryMode,
    send,
    switchSession,
    newSession,
    clearCurrent,
    deleteSession,
  } = useChatSession()

  const [seed, setSeed] = useState('')

  return (
    <div className={styles.app}>
      <Sidebar
        sessions={sessions}
        activeId={sessionId}
        onNew={newSession}
        onSelect={switchSession}
        onDelete={deleteSession}
        onClear={() => void clearCurrent()}
      />
      <div className={styles.column}>
        <ChatView
          messages={messages}
          onHint={(text) => {
            setSeed(text)
          }}
        />
        <Composer
          disabled={sending}
          seed={seed}
          queryMode={queryMode}
          onQueryModeChange={setQueryMode}
          onSend={(text) => {
            setSeed('')
            void send(text)
          }}
        />
      </div>
    </div>
  )
}
