import type { SessionSnapshot } from '../types'
import { THEME } from '../theme'
import { FlashOverlay } from '../components/FlashOverlay'

interface Props { snapshot: SessionSnapshot }

export function CountdownScreen({ snapshot }: Props) {
  const remaining = snapshot.countdown_remaining_ms ?? 0
  const seconds = Math.ceil(remaining / 1000)
  const display = seconds <= 0 ? 'GO!' : String(Math.min(3, seconds))
  const goTrigger = display === 'GO!' ? 'go' : null
  return (
    <>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <div style={{
          fontFamily: THEME.fontDisplay,
          fontSize: '24vw',
          color: display === 'GO!' ? THEME.accent : THEME.text,
          textShadow: display === 'GO!' ? `0 0 40px ${THEME.accent}` : `0 0 28px ${THEME.p1}, 0 0 28px ${THEME.p2}`,
        }}>
          {display}
        </div>
      </div>
      <FlashOverlay text="GO!" color={THEME.accent} trigger={goTrigger} />
    </>
  )
}
