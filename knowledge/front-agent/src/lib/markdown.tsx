import type { ReactNode } from 'react'

/** Inline: **bold** / *italic* / `code` / [text](url) */
function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = []
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g
  let last = 0
  let m: RegExpExecArray | null
  let i = 0

  while ((m = re.exec(text)) !== null) {
    if (m.index > last) {
      nodes.push(text.slice(last, m.index))
    }
    const token = m[0]
    const key = `${keyPrefix}-${i++}`
    if (token.startsWith('**')) {
      nodes.push(<strong key={key}>{token.slice(2, -2)}</strong>)
    } else if (token.startsWith('*')) {
      nodes.push(<em key={key}>{token.slice(1, -1)}</em>)
    } else if (token.startsWith('`')) {
      nodes.push(<code key={key}>{token.slice(1, -1)}</code>)
    } else if (token.startsWith('[')) {
      const link = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/)
      if (link) {
        nodes.push(
          <a key={key} href={link[2]} target="_blank" rel="noopener noreferrer">
            {link[1]}
          </a>,
        )
      } else {
        nodes.push(token)
      }
    }
    last = m.index + token.length
  }
  if (last < text.length) nodes.push(text.slice(last))
  return nodes
}

type OlItem = { n: number; text: string }

type Block =
  | { type: 'p'; text: string }
  | { type: 'h'; level: 2 | 3; text: string }
  | { type: 'ul'; items: string[] }
  | { type: 'ol'; items: OlItem[] }
  | { type: 'quote'; text: string }

function peekNonEmpty(lines: string[], from: number): { index: number; text: string } | null {
  let j = from
  while (j < lines.length && !lines[j].trim()) j += 1
  if (j >= lines.length) return null
  return { index: j, text: lines[j].trim() }
}

function parseBlocks(source: string): Block[] {
  const lines = String(source || '').replace(/\r\n/g, '\n').split('\n')
  const blocks: Block[] = []
  let i = 0

  while (i < lines.length) {
    const trimmed = lines[i].trim()

    if (!trimmed) {
      i += 1
      continue
    }

    if (/^###\s+/.test(trimmed)) {
      blocks.push({ type: 'h', level: 3, text: trimmed.replace(/^###\s+/, '') })
      i += 1
      continue
    }
    if (/^##\s+/.test(trimmed)) {
      blocks.push({ type: 'h', level: 2, text: trimmed.replace(/^##\s+/, '') })
      i += 1
      continue
    }
    if (/^>\s?/.test(trimmed)) {
      const parts: string[] = []
      while (i < lines.length && /^>\s?/.test(lines[i].trim() || '')) {
        parts.push(lines[i].trim().replace(/^>\s?/, ''))
        i += 1
      }
      blocks.push({ type: 'quote', text: parts.join('\n') })
      continue
    }
    if (/^[-*]\s+/.test(trimmed)) {
      const items: string[] = []
      while (i < lines.length && /^[-*]\s+/.test(lines[i].trim() || '')) {
        items.push(lines[i].trim().replace(/^[-*]\s+/, ''))
        i += 1
      }
      blocks.push({ type: 'ul', items })
      continue
    }
    if (/^\d+\.\s+/.test(trimmed)) {
      const items: OlItem[] = []
      while (i < lines.length) {
        const nextItem = peekNonEmpty(lines, i)
        if (!nextItem || !/^\d+\.\s+/.test(nextItem.text)) break

        i = nextItem.index
        const matched = nextItem.text.match(/^(\d+)\.\s+([\s\S]*)$/)
        const n = matched ? Number(matched[1]) : items.length + 1
        const title = matched ? matched[2] : nextItem.text
        items.push({ n, text: title })
        i += 1

        // absorb nested bullets / indented lines; blank lines allowed
        while (i < lines.length) {
          const peek = peekNonEmpty(lines, i)
          if (!peek) {
            i = lines.length
            break
          }
          if (/^\d+\.\s+/.test(peek.text)) break
          if (/^#{1,3}\s+/.test(peek.text)) break
          if (/^>\s?/.test(peek.text)) break
          if (/^[-*]\s+/.test(peek.text) || /^\s{2,}\S/.test(lines[peek.index])) {
            i = peek.index
            const nestTrim = lines[i].trim()
            items[items.length - 1].text +=
              '\n' + nestTrim.replace(/^[-*]\s+/, '· ')
            i += 1
            continue
          }
          break
        }
      }
      blocks.push({ type: 'ol', items })
      continue
    }

    const parts: string[] = [trimmed]
    i += 1
    while (i < lines.length) {
      const next = lines[i].trim()
      if (
        !next ||
        /^#{1,3}\s+/.test(next) ||
        /^[-*]\s+/.test(next) ||
        /^\d+\.\s+/.test(next) ||
        /^>\s?/.test(next)
      ) {
        break
      }
      parts.push(next)
      i += 1
    }
    blocks.push({ type: 'p', text: parts.join('\n') })
  }

  return blocks
}

interface Props {
  source: string
  className?: string
}

export function Markdown({ source, className }: Props) {
  const blocks = parseBlocks(source)

  return (
    <div className={className}>
      {blocks.map((b, idx) => {
        const key = `b-${idx}`
        if (b.type === 'h') {
          const Tag = b.level === 2 ? 'h2' : 'h3'
          return (
            <Tag key={key} className={`md-h md-h${b.level}`}>
              {renderInline(b.text, key)}
            </Tag>
          )
        }
        if (b.type === 'p') {
          return (
            <p key={key} className="md-p">
              {renderInline(b.text, key)}
            </p>
          )
        }
        if (b.type === 'quote') {
          return (
            <blockquote key={key} className="md-quote">
              {renderInline(b.text, key)}
            </blockquote>
          )
        }
        if (b.type === 'ul') {
          return (
            <ul key={key} className="md-ul">
              {b.items.map((item, j) => (
                <li key={`${key}-${j}`}>{renderInline(item, `${key}-${j}`)}</li>
              ))}
            </ul>
          )
        }
        return (
          <ol key={key} className="md-ol">
            {b.items.map((item, j) => (
              <li key={`${key}-${j}`}>
                <span className="md-step-index" aria-hidden>
                  {item.n}
                </span>
                <div className="md-step-body">
                  {item.text.split('\n').map((line, li) => (
                    <div key={`${key}-${j}-l${li}`} className={li > 0 ? 'md-step-line' : undefined}>
                      {renderInline(line, `${key}-${j}-${li}`)}
                    </div>
                  ))}
                </div>
              </li>
            ))}
          </ol>
        )
      })}
      {blocks.length === 0 && source.trim() ? (
        <p className="md-p">{renderInline(source, 'fallback')}</p>
      ) : null}
    </div>
  )
}
