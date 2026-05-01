import type { ReactNode } from 'react'
import { Skeleton } from './Skeleton'
import type { Pose } from '../types'
import { type PlayerId, playerColor } from '../theme'

interface PlayerHalfProps {
  side: 'left' | 'right'
  playerId: PlayerId
  pose: Pose | null
  width: number
  height: number
  /** Per-game overlay drawn behind the skeleton */
  background?: ReactNode
  /** Per-game overlay drawn in front of the skeleton */
  foreground?: ReactNode
  /** Per-player score / metric shown in the corner */
  cornerLabel?: ReactNode
}

export function PlayerHalf({
  side, playerId, pose, width, height, background, foreground, cornerLabel,
}: PlayerHalfProps) {
  const fromXMin = side === 'left' ? 0.0 : 0.5
  const fromXMax = side === 'left' ? 0.5 : 1.0
  const color = playerColor(playerId)

  return (
    <div
      style={{
        position: 'absolute',
        top: 0, bottom: 0,
        left: side === 'left' ? 0 : '50%',
        width: '50%',
        overflow: 'hidden',
      }}
    >
      <div style={{ position: 'absolute', inset: 0 }}>{background}</div>
      <div style={{ position: 'absolute', inset: 0 }}>
        <Skeleton pose={pose} fromXMin={fromXMin} fromXMax={fromXMax} color={color} width={width} height={height} />
      </div>
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>{foreground}</div>
      {cornerLabel && (
        <div
          style={{
            position: 'absolute',
            bottom: 24,
            [side === 'left' ? 'left' : 'right']: 32,
            color,
            textShadow: `0 0 10px ${color}`,
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 36,
            fontWeight: 700,
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {cornerLabel}
        </div>
      )}
    </div>
  )
}
