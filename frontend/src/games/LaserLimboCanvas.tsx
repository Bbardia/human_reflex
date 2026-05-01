import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import type { LaserLimboState, LaserDescriptor } from '../types'
import { THEME } from '../theme'

interface Props {
  state: LaserLimboState
  side: 'left' | 'right'
  width: number
  height: number
}

/** Compute laser line position (0..1 in half-screen) at the given local clock.
 *  Returns null if the laser is not currently visible. */
function laserPosition(laser: LaserDescriptor, clockMs: number): number | null {
  const t = (clockMs - laser.spawn_ms) / laser.duration_ms
  if (t < 0 || t > 1) return null
  const span = 1.0 + 2.0 * laser.thickness
  if (laser.direction === 1) {
    return -laser.thickness + t * span
  }
  return 1.0 + laser.thickness - t * span
}

export function LaserLimboCanvas({ state, side }: Props) {
  // We don't share a clock with the backend; we drive the laser animation
  // with a local rAF clock that's reset whenever the snapshot changes.
  // The backend's `spawn_ms` is in its own monotonic time; we approximate by
  // using the most recent laser's spawn_ms as our reference and walking forward
  // with rAF deltas. This gives smooth motion even between WS ticks.
  const [clockMs, setClockMs] = useState<number>(() => Date.now())
  useEffect(() => {
    let raf = 0
    const tick = () => {
      setClockMs(Date.now())
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [])

  // Establish a local→backend offset using the most-recent laser's spawn_ms.
  // If we have no lasers, fall back to clockMs for both sides; offset stays 0.
  const referenceSpawn = state.lasers[state.lasers.length - 1]?.spawn_ms ?? null
  const localOffset = referenceSpawn != null ? clockMs - referenceSpawn : 0

  const hp = side === 'left' ? state.p1_hp : state.p2_hp
  const startingHp = state.starting_hp

  return (
    <div style={{ position: 'absolute', inset: 0 }}>
      {/* Lasers */}
      {state.lasers.map((laser, i) => {
        const localBackend = clockMs - localOffset
        const pos = laserPosition(laser, localBackend)
        if (pos == null) return null
        return <Laser key={`${laser.spawn_ms}-${i}`} laser={laser} pos={pos} />
      })}

      {/* HP indicator at top */}
      <div style={{
        position: 'absolute', top: '12%', left: 0, right: 0, textAlign: 'center',
        display: 'flex', justifyContent: 'center', gap: 12,
      }}>
        {Array.from({ length: startingHp }).map((_, i) => (
          <div key={i} style={{
            width: 24, height: 24, borderRadius: '50%',
            background: i < hp ? (side === 'left' ? THEME.p1 : THEME.p2) : 'rgba(255,255,255,0.15)',
            boxShadow: i < hp ? (side === 'left' ? THEME.glowP1 : THEME.glowP2) : 'none',
          }} />
        ))}
      </div>

      {/* Out-of-HP overlay */}
      {hp <= 0 && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: THEME.fontDisplay, fontSize: 64, color: '#ff3344',
          textShadow: '0 0 24px #ff3344',
          background: 'rgba(255,0,0,0.05)',
        }}>OUT</div>
      )}
    </div>
  )
}

function Laser({ laser, pos }: { laser: LaserDescriptor; pos: number }) {
  // Render the laser as a glowing band at its current position.
  const isHorizontal = laser.orientation === 'h'
  const thicknessPct = laser.thickness * 200  // visual strip slightly thicker than collision
  const positionPct = pos * 100

  const baseStyle: CSSProperties = {
    position: 'absolute',
    background: `linear-gradient(${isHorizontal ? '180deg' : '90deg'}, transparent, ${THEME.target}, transparent)`,
    boxShadow: `0 0 20px ${THEME.target}`,
    pointerEvents: 'none',
  }

  if (isHorizontal) {
    return <div style={{
      ...baseStyle,
      left: 0, right: 0,
      top: `calc(${positionPct}% - ${thicknessPct / 2}%)`,
      height: `${thicknessPct}%`,
    }} />
  }
  return <div style={{
    ...baseStyle,
    top: 0, bottom: 0,
    left: `calc(${positionPct}% - ${thicknessPct / 2}%)`,
    width: `${thicknessPct}%`,
  }} />
}
