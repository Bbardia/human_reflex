import { useEffect, useState } from 'react'

interface FlashOverlayProps {
  text: string
  color: string
  trigger: string | number | null
  durationMs?: number
}

export function FlashOverlay({ text, color, trigger, durationMs = 800 }: FlashOverlayProps) {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    if (trigger == null) return
    setVisible(true)
    const t = setTimeout(() => setVisible(false), durationMs)
    return () => clearTimeout(t)
  }, [trigger, durationMs])

  if (!visible) return null

  return (
    <>
      <style>{`
        @keyframes flash-in-out {
          0% { opacity: 0; transform: scale(0.6); }
          25% { opacity: 1; transform: scale(1.05); }
          75% { opacity: 1; transform: scale(1.0); }
          100% { opacity: 0; transform: scale(1.1); }
        }
      `}</style>
      <div style={{
        position: 'absolute', inset: 0, zIndex: 100,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        pointerEvents: 'none',
      }}>
        <div style={{
          fontFamily: "'Audiowide', system-ui, sans-serif",
          fontSize: '14vw',
          color, textShadow: `0 0 32px ${color}, 0 0 64px ${color}`,
          letterSpacing: '0.05em',
          animation: `flash-in-out ${durationMs}ms ease-out forwards`,
        }}>{text}</div>
      </div>
    </>
  )
}
