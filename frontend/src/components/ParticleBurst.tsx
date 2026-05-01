import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'

interface ParticleBurstProps {
  /** Centre point in the parent's percentage coords (0-100). */
  xPct: number
  yPct: number
  color: string
  /** A token that, when changed, restarts the burst. */
  trigger: string | number | null
  count?: number
}

interface Particle {
  angle: number
  distance: number
  delay: number
}

/** Self-extinguishing radial burst. */
export function ParticleBurst({ xPct, yPct, color, trigger, count = 14 }: ParticleBurstProps) {
  const [particles, setParticles] = useState<Particle[]>([])

  useEffect(() => {
    if (trigger == null) return
    const ps: Particle[] = []
    for (let i = 0; i < count; i++) {
      ps.push({
        angle: (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.4,
        distance: 60 + Math.random() * 40,
        delay: Math.random() * 60,
      })
    }
    setParticles(ps)
    const t = setTimeout(() => setParticles([]), 700)
    return () => clearTimeout(t)
  }, [trigger, count])

  if (particles.length === 0) return null

  return (
    <>
      <style>{`
        @keyframes particle-burst {
          0% { transform: translate(0, 0); opacity: 1; }
          100% { transform: translate(var(--dx), var(--dy)); opacity: 0; }
        }
      `}</style>
      <div style={{
        position: 'absolute',
        left: `${xPct}%`,
        top: `${yPct}%`,
        width: 0, height: 0,
        pointerEvents: 'none',
      }}>
        {particles.map((p, i) => {
          const dx = Math.cos(p.angle) * p.distance
          const dy = Math.sin(p.angle) * p.distance
          const style: CSSProperties = {
            position: 'absolute',
            left: -3, top: -3,
            width: 6, height: 6,
            borderRadius: '50%',
            background: color,
            boxShadow: `0 0 8px ${color}`,
            animation: `particle-burst 600ms ${p.delay}ms ease-out forwards`,
            ['--dx' as string]: `${dx}px`,
            ['--dy' as string]: `${dy}px`,
          } as CSSProperties
          return <div key={`${trigger}-${i}`} style={style} />
        })}
      </div>
    </>
  )
}
