import type { SessionSnapshot } from '../types'
import { GestureRing } from '../components/GestureRing'
import { THEME, playerColor } from '../theme'

interface Props { snapshot: SessionSnapshot }

export function SummaryScreen({ snapshot }: Props) {
  const summary = snapshot.summary
  if (!summary) return null
  const winnerId = summary.winner
  const winnerLabel = winnerId == null ? 'DRAW' : `PLAYER ${winnerId}`
  const winnerColor = winnerId == null ? THEME.accent : playerColor(winnerId as 1 | 2)

  return (
    <div style={{
      position: 'absolute', inset: 0,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap: 48,
    }}>
      <div style={{
        fontFamily: THEME.fontMono, fontSize: 22, color: THEME.dim, letterSpacing: '0.2em',
      }}>
        {summary.name.toUpperCase()}
      </div>
      <div style={{
        fontFamily: THEME.fontDisplay, fontSize: '8vw',
        color: winnerColor,
        textShadow: `0 0 36px ${winnerColor}`,
      }}>
        {winnerLabel} WINS
      </div>
      <div style={{ display: 'flex', gap: 80, fontFamily: THEME.fontMono, fontSize: 28 }}>
        <div style={{ color: THEME.p1, textShadow: THEME.glowP1 }}>
          <div style={{ fontSize: 14, letterSpacing: '0.2em', opacity: 0.7 }}>P1</div>
          <div style={{ fontVariantNumeric: 'tabular-nums', fontSize: 48 }}>
            {summary.p1_metric ?? '—'}
          </div>
          <div style={{ fontSize: 12, opacity: 0.6 }}>{summary.metric_unit}</div>
        </div>
        <div style={{ color: THEME.p2, textShadow: THEME.glowP2 }}>
          <div style={{ fontSize: 14, letterSpacing: '0.2em', opacity: 0.7 }}>P2</div>
          <div style={{ fontVariantNumeric: 'tabular-nums', fontSize: 48 }}>
            {summary.p2_metric ?? '—'}
          </div>
          <div style={{ fontSize: 12, opacity: 0.6 }}>{summary.metric_unit}</div>
        </div>
      </div>
      <GestureRing progress={snapshot.gesture_progress} size={200} label="HANDS UP TO PLAY AGAIN" />
    </div>
  )
}
