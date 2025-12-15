import * as Icons from '@lobehub/icons'
import CustomLogo from '@/assets/customAI.png'
import { useEffect, useMemo, useState } from 'react'

interface AILogoProps {
  name: string // 图标名称（区分大小写！如 OpenAI、DeepSeek）或图标URL
  baseUrl?: string
  style?: 'Color' | 'Text' | 'Outlined' | 'Glyph'
  size?: number
}

const AILogo = ({ name, baseUrl, style = 'Color', size = 24 }: AILogoProps) => {
  const trimmedName = (name || '').trim()
  const isUrl =
    trimmedName.startsWith('http://') || trimmedName.startsWith('https://') || trimmedName.startsWith('data:image')

  const faviconCandidates = useMemo(() => {
    const candidates: string[] = []

    if (trimmedName && isUrl) {
      candidates.push(trimmedName)
    }

    if (baseUrl) {
      try {
        const u = new URL(baseUrl)
        candidates.push(`${u.origin}/favicon.ico`)
        candidates.push(`${u.origin}/favicon.png`)

        const parts = u.hostname.split('.')
        if (parts.length >= 2) {
          const root = parts.slice(-2).join('.')
          candidates.push(`${u.protocol}//${root}/favicon.ico`)
          candidates.push(`${u.protocol}//${root}/favicon.png`)
        }
      } catch {
        // ignore
      }
    }

    return Array.from(new Set(candidates))
  }, [baseUrl, isUrl, trimmedName])

  const [imgIndex, setImgIndex] = useState(0)
  const [imgSrc, setImgSrc] = useState<string>(faviconCandidates[0] || CustomLogo)

  useEffect(() => {
    setImgIndex(0)
    setImgSrc(faviconCandidates[0] || CustomLogo)
  }, [faviconCandidates.join('|')])

  const renderImg = () => {
    return (
      <span style={{ fontSize: size }}>
        <img
          src={imgSrc}
          alt="Provider Logo"
          style={{ width: size, height: size, objectFit: 'contain' }}
          onError={() => {
            const next = imgIndex + 1
            if (next < faviconCandidates.length) {
              setImgIndex(next)
              setImgSrc(faviconCandidates[next])
              return
            }
            setImgSrc(CustomLogo)
          }}
        />
      </span>
    )
  }

  if (!trimmedName || trimmedName === 'custom') {
    return renderImg()
  }

  if (isUrl) {
    return renderImg()
  }

  const Icon = Icons[trimmedName as keyof typeof Icons]
  if (!Icon) {
    return faviconCandidates.length ? renderImg() : (
      <span style={{ fontSize: size }}>
        <img src={CustomLogo} alt="CustomLogo" style={{ width: size, height: size }} />
      </span>
    )
  }

  const Variant = Icon[style as keyof typeof Icon]
  if (!Variant) {
    return <Icon size={size} />
  }

  return <Variant size={size} />
}

export default AILogo
