import { THEME } from '../theme'

interface GestureRingProps {
  progress: number  // 0..1
  size?: number
  label?: string
}

export function GestureRing({ progress, size = 240, label }: GestureRingProps) {
  const radius = size / 2 - 12
  const circumference = 2 * Math.PI * radius
  const dashOffset = circumference * (1 - Math.max(0, Math.min(1, progress)))

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} style={{ filter: `drop-shadow(0 0 12px ${THEME.p1})` }}>
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="rgba(255,255,255,0.1)" strokeWidth={6} fill="none" />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          stroke={THEME.p1} strokeWidth={6} fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      {label && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: THEME.p1, textShadow: THEME.glowP1, fontFamily: THEME.fontDisplay,
          fontSize: 18, letterSpacing: '0.15em', textAlign: 'center', padding: 16,
        }}>{label}</div>
      )}
    </div>
  )
}
