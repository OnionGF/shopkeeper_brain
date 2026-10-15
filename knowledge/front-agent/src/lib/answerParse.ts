function isImageUrl(url: string): boolean {
  try {
    const u = new URL(url)
    return /\.(png|jpe?g|gif|webp|bmp|svg)$/i.test(u.pathname)
  } catch {
    return /\.(png|jpe?g|gif|webp|bmp|svg)(\?|#|$)/i.test(url || '')
  }
}

function normalizeUrl(rawUrl: string): string {
  return String(rawUrl || '')
    .trim()
    .replace(/\s/g, '%20')
}

function extractUrlsLoose(text: string): string[] {
  const matches = String(text || '').match(/(https?:\/\/[^\s]+)/g) || []
  const trimTail = (u: string) => u.replace(/[)\]}'">，。,;；\]】）＞]+$/g, '')
  const trimHead = (u: string) => u.replace(/^[<([{'"]+|^[＜（【\[]+/g, '')
  const seen = new Set<string>()
  const out: string[] = []
  for (const m of matches) {
    const u = trimHead(trimTail(m))
    if (!u || seen.has(u)) continue
    seen.add(u)
    out.push(u)
  }
  return out
}

function findLastImageMarkerIndex(raw: string): { idx: number; len: number } {
  const re = /【\s*图片\s*】|\[\s*图片\s*\]/g
  let m: RegExpExecArray | null
  let lastIdx = -1
  let lastLen = 0
  while ((m = re.exec(raw)) !== null) {
    lastIdx = m.index
    lastLen = m[0].length
  }
  return { idx: lastIdx, len: lastLen }
}

export function parseAnswerAndImages(
  text: string,
  candidateImageUrls: string[] = [],
): { text: string; images: string[] } {
  const raw = String(text || '')
  const { idx, len } = findLastImageMarkerIndex(raw)
  let displayText = raw
  const imagesFromBlock: string[] = []

  if (idx !== -1) {
    displayText = raw.slice(0, idx).trimEnd()
    const after = raw.slice(idx + len).trim()
    for (const line of after.split(/\r?\n/).map((l) => l.trim()).filter(Boolean)) {
      if (line.startsWith('http://') || line.startsWith('https://')) {
        imagesFromBlock.push(line)
      } else {
        imagesFromBlock.push(...extractUrlsLoose(line))
      }
    }
  }

  const candidates = candidateImageUrls.map(normalizeUrl).filter(isImageUrl)
  const loose = extractUrlsLoose(raw).map(normalizeUrl).filter(isImageUrl)
  const block = imagesFromBlock.map(normalizeUrl).filter(isImageUrl)

  const seen = new Set<string>()
  const images: string[] = []
  for (const u of [...block, ...candidates, ...loose]) {
    if (seen.has(u)) continue
    seen.add(u)
    images.push(u)
  }

  return { text: displayText, images }
}
