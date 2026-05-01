import { useEffect, useState } from 'react'
import type { TouchCircleState, RoundResult } from '../types'
import { THEME } from '../theme'
import { ParticleBurst } from '../components/ParticleBurst'

interface Props {
  state: TouchCircleState
  side: 'left' | 'right'
  width: number
  height: number
}

/** Renders the half-screen overlay for one player: target, live time, false-start indicator. */
export function TouchCircleCanvas({ state, side, width: _width, height: _height }: Props) {
  const showTarget = state.phase === 'active' && state.target
  const target = state.target

  const lastResult: RoundResult | undefined = state.results[state.results.length - 1]
  const playerKey = side === 'left' ? 'p1' : 'p2'
  const playerTime = lastResult?.[`${playerKey}_time_ms`] ?? null
  const falseStart = lastResult?.[`${playerKey}_false_start`] ?? false

  const [lastBurstRound, setLastBurstRound] = useState<number | null>(null)
  useEffect(() => {
    if (playerTime !== null && !falseStart && state.round !== lastBurstRound) {
      setLastBurstRound(state.round)
    }
  }, [playerTime, falseStart, state.round, lastBurstRound])

  const burstColor = side === 'left' ? THEME.p1 : THEME.p2

  return (
    <div style={{ position: 'absolute', inset: 0 }}>
      {showTarget && target && (
        <div
          style={{
            position: 'absolute',
            left: `${target.x * 100}%`,
            top: `${target.y * 100}%`,
            transform: 'translate(-50%, -50%)',
            width: `${target.radius * 2 * 100}%`,
            aspectRatio: '1',
            borderRadius: '50%',
            background: `radial-gradient(${THEME.target}, #500020)`,
            boxShadow: `0 0 32px ${THEME.target}, inset 0 0 16px rgba(255,255,255,0.4)`,
            animation: 'pulse 0.8s ease-in-out infinite alternate',
          }}
        />
      )}
      {state.phase === 'preroll' && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: THEME.fontMono, fontSize: 28, color: THEME.dim, letterSpacing: '0.2em',
        }}>
          GET READY
        </div>
      )}
      {falseStart && (
        <div style={{
          position: 'absolute', top: '20%', left: 0, right: 0, textAlign: 'center',
          fontFamily: THEME.fontDisplay, fontSize: 36, color: '#ff3344',
          textShadow: '0 0 12px #ff3344',
        }}>FALSE START</div>
      )}
      {playerTime !== null && !falseStart && (
        <div style={{
          position: 'absolute', top: '14%', left: 0, right: 0, textAlign: 'center',
          fontFamily: THEME.fontMono, fontSize: 38,
          color: side === 'left' ? THEME.p1 : THEME.p2,
          textShadow: side === 'left' ? THEME.glowP1 : THEME.glowP2,
        }}>{playerTime}ms</div>
      )}
      {target && (
        <ParticleBurst
          xPct={target.x * 100}
          yPct={target.y * 100}
          color={burstColor}
          trigger={lastBurstRound}
        />
      )}
      <style>{`@keyframes pulse { from { transform: translate(-50%,-50%) scale(0.96); } to { transform: translate(-50%,-50%) scale(1.04); } }`}</style>
    </div>
  )
}
