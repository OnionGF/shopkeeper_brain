import { useRef, useState } from 'react'
import styles from './DropZone.module.css'

interface Props {
  onFiles: (files: FileList | File[]) => void
}

export function DropZone({ onFiles }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragover, setDragover] = useState(false)

  return (
    <div
      className={`${styles.zone} ${dragover ? styles.dragover : ''}`}
      role="button"
      tabIndex={0}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          inputRef.current?.click()
        }
      }}
      onDragOver={(e) => {
        e.preventDefault()
        setDragover(true)
      }}
      onDragLeave={(e) => {
        e.preventDefault()
        setDragover(false)
      }}
      onDrop={(e) => {
        e.preventDefault()
        setDragover(false)
        if (e.dataTransfer.files?.length) onFiles(e.dataTransfer.files)
      }}
    >
      <div className={styles.icon}>↑</div>
      <div className={styles.text}>点击或拖拽文件到此处</div>
      <div className={styles.hint}>支持 .pdf / .md</div>
      <input
        ref={inputRef}
        className={styles.input}
        type="file"
        accept=".pdf,.md"
        multiple
        onChange={(e) => {
          if (e.target.files?.length) onFiles(e.target.files)
          e.target.value = ''
        }}
      />
    </div>
  )
}
