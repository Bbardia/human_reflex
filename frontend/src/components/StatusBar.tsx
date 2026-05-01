import { THEME } from '../theme'

interface StatusBarProps {
  left?: string
  center?: string
  right?: string
}

export function StatusBar({ left, center, right }: StatusBarProps) {
  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0, height: '8%',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 32px',
      background: 'linear-gradient(180deg, rgba(0,0,0,0.5), transparent)',
      borderBottom: '1px solid rgba(255,255,255,0.06)',
      fontFamily: "'JetBrains Mono', monospace",
      letterSpacing: '0.1em',
      fontSize: 18,
      zIndex: 10,
    }}>
      <span style={{ color: THEME.p1, textShadow: THEME.glowP1 }}>{left ?? 'PLAYER 1'}</span>
      <span style={{ color: THEME.accent, textShadow: `0 0 10px ${THEME.accent}` }}>{center ?? ''}</span>
      <span style={{ color: THEME.p2, textShadow: THEME.glowP2 }}>{right ?? 'PLAYER 2'}</span>
    </div>
  )
}
