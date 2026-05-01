import { useEffect, useState } from 'react'
import type { GoalieState } from '../types'
import { THEME } from '../theme'
import { ParticleBurst } from '../components/ParticleBurst'

interface Props {
  state: GoalieState
  side: 'left' | 'right'
  width: number
  height: number
}

/** Renders the half-screen overlay for one player: the 5 zones (faintly outlined),
 *  the ball traveling toward its zone, and the live save indicator. */
export function GoalieCanvas({ state, side }: Props) {
  const lastResult = state.results[state.results.length - 1]
  const saved = side === 'left'
    ? lastResult?.p1_saved ?? false
    : lastResult?.p2_saved ?? false
  const saveTime = side === 'left'
    ? lastResult?.p1_save_time_ms ?? null
    : lastResult?.p2_save_time_ms ?? null

  const ball = state.ball
  const targetZone = ball ? state.zones[ball.zone] : null

  const [burstShot, setBurstShot] = useState<number | null>(null)
  useEffect(() => {
    if (saved && state.shot !== burstShot) {
      setBurstShot(state.shot)
    }
  }, [saved, state.shot, burstShot])

  const burstColor = side === 'left' ? THEME.p1 : THEME.p2
  const burstZoneIdx = state.results[state.results.length - 1]?.zone
  const burstZone = burstZoneIdx != null ? state.zones[burstZoneIdx] : null
  const burstX = burstZone ? (burstZone[0] + burstZone[2]) * 50 : 50
  const burstY = burstZone ? (burstZone[1] + burstZone[3]) * 50 : 50

  return (
    <div style={{ position: 'absolute', inset: 0 }}>
      {/* Faint zone outlines, always visible during active phase */}
      {state.phase === 'active' && state.zones.map((z, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: `${z[0] * 100}%`,
            top: `${z[1] * 100}%`,
            width: `${(z[2] - z[0]) * 100}%`,
            height: `${(z[3] - z[1]) * 100}%`,
            border: `1px dashed rgba(255,255,255,${ball && i === ball.zone ? 0.5 : 0.12})`,
            borderRadius: 8,
            boxShadow: ball && i === ball.zone ? `0 0 24px ${THEME.target}` : 'none',
            pointerEvents: 'none',
          }}
        />
      ))}

      {/* Ball: starts at top-center of the half, animates to target zone center */}
      {ball && targetZone && (
        <div
          key={`ball-${state.shot}-${ball.zone}`}
          style={{
            position: 'absolute',
            left: '50%',
            top: '0%',
            width: '8%',
            aspectRatio: '1',
            borderRadius: '50%',
            background: `radial-gradient(${THEME.target}, #500020)`,
            boxShadow: `0 0 28px ${THEME.target}, inset 0 0 12px rgba(255,255,255,0.4)`,
            transform: 'translate(-50%, 0)',
            animation: `goalie-ball-${ball.zone} ${ball.travel_ms}ms ease-out forwards`,
          }}
        />
      )}

      {/* GET READY during preroll */}
      {state.phase === 'preroll' && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: THEME.fontMono, fontSize: 28, color: THEME.dim, letterSpacing: '0.2em',
        }}>
          GET READY
        </div>
      )}

      {/* Live save indicator at top of half */}
      {saved && (
        <div style={{
          position: 'absolute', top: '14%', left: 0, right: 0, textAlign: 'center',
          fontFamily: THEME.fontDisplay, fontSize: 36,
          color: side === 'left' ? THEME.p1 : THEME.p2,
          textShadow: side === 'left' ? THEME.glowP1 : THEME.glowP2,
        }}>SAVE! {saveTime}ms</div>
      )}

      {/* Define keyframes for each zone target */}
      {ball && targetZone && (
        <style>{`
          @keyframes goalie-ball-${ball.zone} {
            from { left: 50%; top: 0%; }
            to {
              left: ${(targetZone[0] + targetZone[2]) * 50}%;
              top: ${(targetZone[1] + targetZone[3]) * 50}%;
            }
          }
        `}</style>
      )}
      <ParticleBurst xPct={burstX} yPct={burstY} color={burstColor} trigger={burstShot} />
    </div>
  )
}
