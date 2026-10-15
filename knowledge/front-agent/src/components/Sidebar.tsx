import { Link } from 'react-router-dom'
import type { SessionMeta } from '../types'
import styles from './Sidebar.module.css'

interface Props {
  sessions: SessionMeta[]
  activeId: string
  onNew: () => void
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onClear: () => void
}

export function Sidebar({ sessions, activeId, onNew, onSelect, onDelete, onClear }: Props) {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <div className={styles.logo} aria-hidden />
        <div className={styles.brandText}>
          <div className={styles.brandName}>Agent Brain</div>
          <div className={styles.brandSub}>Tool · RAG · Web</div>
        </div>
      </div>

      <Link className={styles.navImport} to="/import">
        <span className={styles.newFull}>知识库导入</span>
        <span className={styles.newShort} aria-hidden>
          ↑
        </span>
      </Link>

      <button type="button" className={styles.newBtn} onClick={onNew}>
        <span className={styles.newFull}>+ 新会话</span>
        <span className={styles.newShort} aria-hidden>
          +
        </span>
      </button>

      <div className={styles.list}>
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`${styles.item} ${s.id === activeId ? styles.itemActive : ''}`}
          >
            <button type="button" className={styles.itemBtn} onClick={() => onSelect(s.id)}>
              {s.title}
            </button>
            <button
              type="button"
              className={styles.delBtn}
              aria-label="删除会话"
              onClick={() => onDelete(s.id)}
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <div className={styles.foot}>
        <button type="button" className={styles.clearBtn} onClick={onClear}>
          清空当前会话
        </button>
      </div>
    </aside>
  )
}
