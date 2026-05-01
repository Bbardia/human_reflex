import type { SessionSnapshot } from '../types'
import { GestureRing } from '../components/GestureRing'
import { THEME } from '../theme'

interface Props { snapshot: SessionSnapshot }

export function TitleScreen({ snapshot }: Props) {
  return (
    <div style={{
      position: 'absolute', inset: 0,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap: 64,
    }}>
      <h1 style={{
        margin: 0, fontFamily: THEME.fontDisplay, fontSize: '8vw',
        color: THEME.text,
        textShadow: `0 0 18px ${THEME.p1}, 0 0 36px ${THEME.p2}`,
        letterSpacing: '0.1em',
      }}>
        HUMAN REFLEX
      </h1>
      <div style={{ color: THEME.dim, fontFamily: THEME.fontMono, fontSize: 24, letterSpacing: '0.2em' }}>
        TWO PLAYERS · POSE-DRIVEN
      </div>
      <GestureRing progress={snapshot.gesture_progress} size={280}
        label="PLAYER 1: RAISE BOTH HANDS TO START"
      />
    </div>
  )
}
