import type { SessionSnapshot } from '../types'
import { GestureRing } from '../components/GestureRing'
import { THEME, playerColor } from '../theme'

interface Props { snapshot: SessionSnapshot }

export function IntermissionScreen({ snapshot }: Props) {
  const data = snapshot.intermission
  if (!data) return null
  const last = data.last_summary
  const winnerId = last?.winner ?? null
  const winnerLabel = winnerId == null ? 'DRAW' : `PLAYER ${winnerId}`
  const winnerColor = winnerId == null ? THEME.accent : playerColor(winnerId as 1 | 2)

  return (
    <div style={{
      position: 'absolute', inset: 0,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap: 32,
    }}>
      <div style={{
        fontFamily: THEME.fontMono, fontSize: 16, color: THEME.dim, letterSpacing: '0.2em',
      }}>
        GAME {data.current_index - 1} / {data.total_games} · COMPLETE
      </div>

      {last && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 48,
          fontFamily: THEME.fontMono,
        }}>
          <div style={{ color: THEME.p1, textShadow: THEME.glowP1, textAlign: 'center' }}>
            <div style={{ fontSize: 12, opacity: 0.7, letterSpacing: '0.2em' }}>P1</div>
            <div style={{ fontSize: 40, fontVariantNumeric: 'tabular-nums' }}>
              {last.p1_metric ?? '—'}
            </div>
          </div>
          <div style={{
            fontFamily: THEME.fontDisplay, fontSize: '3vw',
            color: winnerColor,
            textShadow: `0 0 24px ${winnerColor}`,
          }}>
            {winnerLabel}
          </div>
          <div style={{ color: THEME.p2, textShadow: THEME.glowP2, textAlign: 'center' }}>
            <div style={{ fontSize: 12, opacity: 0.7, letterSpacing: '0.2em' }}>P2</div>
            <div style={{ fontSize: 40, fontVariantNumeric: 'tabular-nums' }}>
              {last.p2_metric ?? '—'}
            </div>
          </div>
        </div>
      )}

      <div style={{
        marginTop: 24,
        fontFamily: THEME.fontMono, fontSize: 14, color: THEME.dim, letterSpacing: '0.2em',
      }}>
        NEXT
      </div>
      <div style={{
        fontFamily: THEME.fontDisplay, fontSize: '5vw',
        color: THEME.text,
        textShadow: `0 0 18px ${THEME.p1}, 0 0 36px ${THEME.p2}`,
      }}>
        {data.next_game_name ?? '—'}
      </div>

      <GestureRing
        progress={snapshot.gesture_progress}
        size={160}
        label={`AUTO IN ${Math.ceil(data.remaining_ms / 1000)}S · OR HANDS UP`}
      />
    </div>
  )
}
