import type { PoseSimonState, PoseSimonPose } from '../types'
import { THEME } from '../theme'

interface Props {
  state: PoseSimonState
  side: 'left' | 'right'
  width: number
  height: number
}

const POSE_LABEL: Record<PoseSimonPose, string> = {
  arms_up: 'ARMS UP',
  t_pose: 'T-POSE',
  left_arm_up: 'LEFT ARM UP',
  right_arm_up: 'RIGHT ARM UP',
  hands_on_hips: 'HANDS ON HIPS',
  squat: 'SQUAT',
}

const POSE_GLYPH: Record<PoseSimonPose, string> = {
  arms_up: '🙌',
  t_pose: '✝︎',
  left_arm_up: '↖',
  right_arm_up: '↗',
  hands_on_hips: '🦵',
  squat: '🪑',
}

export function PoseSimonCanvas({ state, side }: Props) {
  const playerIndex = side === 'left' ? state.p1_index : state.p2_index
  const playerCompleted = side === 'left' ? state.p1_completed : state.p2_completed

  return (
    <div style={{ position: 'absolute', inset: 0 }}>
      {state.phase === 'demo' && (
        <DemoOverlay sequence={state.sequence} />
      )}

      {state.phase === 'input' && !playerCompleted && (
        <InputOverlay
          sequence={state.sequence}
          currentIndex={playerIndex}
          side={side}
        />
      )}

      {state.phase === 'input' && playerCompleted && (
        <CompletedOverlay side={side} />
      )}

      {state.phase === 'resolve' && (
        <ResolveOverlay
          completed={playerCompleted}
          progress={`${playerIndex} / ${state.sequence.length}`}
        />
      )}
    </div>
  )
}

function DemoOverlay({ sequence }: { sequence: PoseSimonPose[] }) {
  return (
    <div style={{
      position: 'absolute', inset: 0,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap: 16,
    }}>
      <div style={{
        fontFamily: THEME.fontMono, fontSize: 16, color: THEME.dim, letterSpacing: '0.2em',
      }}>WATCH</div>
      <div style={{ display: 'flex', gap: 16 }}>
        {sequence.map((p, i) => (
          <div key={i} style={{
            padding: '12px 16px', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8,
            fontFamily: THEME.fontMono, fontSize: 13, textAlign: 'center', minWidth: 100,
          }}>
            <div style={{ fontSize: 28 }}>{POSE_GLYPH[p]}</div>
            <div style={{ marginTop: 4, opacity: 0.85 }}>{POSE_LABEL[p]}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function InputOverlay({
  sequence, currentIndex, side,
}: { sequence: PoseSimonPose[]; currentIndex: number; side: 'left' | 'right' }) {
  if (currentIndex >= sequence.length) return null
  const target = sequence[currentIndex]
  const color = side === 'left' ? THEME.p1 : THEME.p2
  const glow = side === 'left' ? THEME.glowP1 : THEME.glowP2
  return (
    <div style={{
      position: 'absolute', top: '12%', left: 0, right: 0,
      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10,
    }}>
      <div style={{
        fontFamily: THEME.fontMono, fontSize: 14, color: THEME.dim, letterSpacing: '0.2em',
      }}>POSE {currentIndex + 1} / {sequence.length}</div>
      <div style={{ fontSize: 60, lineHeight: 1 }}>{POSE_GLYPH[target]}</div>
      <div style={{
        fontFamily: THEME.fontDisplay, fontSize: 28,
        color, textShadow: glow, letterSpacing: '0.1em',
      }}>{POSE_LABEL[target]}</div>
    </div>
  )
}

function CompletedOverlay({ side }: { side: 'left' | 'right' }) {
  const color = side === 'left' ? THEME.p1 : THEME.p2
  const glow = side === 'left' ? THEME.glowP1 : THEME.glowP2
  return (
    <div style={{
      position: 'absolute', top: '14%', left: 0, right: 0, textAlign: 'center',
      fontFamily: THEME.fontDisplay, fontSize: 40, color, textShadow: glow,
    }}>NICE!</div>
  )
}

function ResolveOverlay({ completed, progress }: { completed: boolean; progress: string }) {
  return (
    <div style={{
      position: 'absolute', top: '14%', left: 0, right: 0, textAlign: 'center',
      fontFamily: THEME.fontDisplay, fontSize: 40,
      color: completed ? THEME.accent : '#ff3344',
      textShadow: completed ? `0 0 12px ${THEME.accent}` : '0 0 12px #ff3344',
    }}>{completed ? `CLEARED · ${progress}` : `MISSED · ${progress}`}</div>
  )
}
