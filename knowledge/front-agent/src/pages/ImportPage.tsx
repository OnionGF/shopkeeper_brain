import { Link } from 'react-router-dom'
import { DropZone } from '../components/import/DropZone'
import { FileTaskCard } from '../components/import/FileTaskCard'
import { useImportTasks } from '../hooks/useImportTasks'
import styles from './ImportPage.module.css'

export function ImportPage() {
  const { tasks, enqueueFiles } = useImportTasks()

  return (
    <div className={styles.page}>
      <div className={styles.inner}>
        <div className={styles.top}>
          <div className={styles.brand}>
            <div className={styles.logo}>A</div>
            <div className={styles.brandText}>
              <strong>Agent Brain</strong>
              <span>Import · RAG Pipeline</span>
            </div>
          </div>
          <Link className={styles.back} to="/">
            ← 返回问答
          </Link>
        </div>

        <div className={styles.panel}>
          <h1 className={styles.title}>知识库导入</h1>
          <p className={styles.lead}>
            上传 PDF / Markdown，系统会按流水线切分、识别、向量化并入库。
          </p>
          <DropZone onFiles={(files) => void enqueueFiles(files)} />
          <div className={styles.list}>
            {tasks.map((t) => (
              <FileTaskCard key={t.id} task={t} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
