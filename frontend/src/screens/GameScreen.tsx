import { useEffect, useState } from 'react'
import type { SessionSnapshot, GameState } from '../types'
import { PlayerHalf } from '../components/PlayerHalf'
import { StatusBar } from '../components/StatusBar'
import { TouchCircleCanvas } from '../games/TouchCircleCanvas'
import { GoalieCanvas } from '../games/GoalieCanvas'
import { PoseSimonCanvas } from '../games/PoseSimonCanvas'
import { LaserLimboCanvas } from '../games/LaserLimboCanvas'
import { THEME } from '../theme'

interface Props { snapshot: SessionSnapshot }

function gameDisplayName(g: GameState): string {
  switch (g.type) {
    case 'touch_circle': return 'TOUCH THE CIRCLE'
    case 'goalie': return 'GOALIE'
    case 'pose_simon': return 'POSE SIMON'
    case 'laser_limbo': return 'LASER LIMBO'
  }
}

function progressLabel(g: GameState): string {
  switch (g.type) {
    case 'touch_circle': return `ROUND ${g.round} / ${g.total_rounds}`
    case 'goalie': return `SHOT ${g.shot} / ${g.total_shots}`
    case 'pose_simon': return `ROUND ${g.round} · ${g.sequence.length} POSE${g.sequence.length === 1 ? '' : 'S'}`
    case 'laser_limbo': return `${g.p1_hp} HP · ${g.p2_hp} HP`
  }
}

function p1CornerLabel(g: GameState): string {
  switch (g.type) {
    case 'touch_circle': {
      const last = g.results[g.results.length - 1]
      return last?.p1_time_ms != null ? `${last.p1_time_ms}` : ''
    }
    case 'goalie':
      return `${g.results.filter(r => r.p1_saved).length}`
    case 'pose_simon':
      return `${g.rounds_cleared_p1}`
    case 'laser_limbo':
      return `${g.p1_hp}`
  }
}

function p2CornerLabel(g: GameState): string {
  switch (g.type) {
    case 'touch_circle': {
      const last = g.results[g.results.length - 1]
      return last?.p2_time_ms != null ? `${last.p2_time_ms}` : ''
    }
    case 'goalie':
      return `${g.results.filter(r => r.p2_saved).length}`
    case 'pose_simon':
      return `${g.rounds_cleared_p2}`
    case 'laser_limbo':
      return `${g.p2_hp}`
  }
}

function gameForeground(g: GameState, side: 'left' | 'right', width: number, height: number) {
  switch (g.type) {
    case 'touch_circle':
      return <TouchCircleCanvas state={g} side={side} width={width} height={height} />
    case 'goalie':
      return <GoalieCanvas state={g} side={side} width={width} height={height} />
    case 'pose_simon':
      return <PoseSimonCanvas state={g} side={side} width={width} height={height} />
    case 'laser_limbo':
      return <LaserLimboCanvas state={g} side={side} width={width} height={height} />
  }
}

export function GameScreen({ snapshot }: Props) {
  const [size, setSize] = useState({ w: window.innerWidth, h: window.innerHeight })
  useEffect(() => {
    const onResize = () => setSize({ w: window.innerWidth, h: window.innerHeight })
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  const game = snapshot.game
  if (!game) return null

  const halfW = size.w / 2
  const fullH = size.h

  return (
    <div style={{ position: 'absolute', inset: 0 }}>
      <StatusBar
        center={`${gameDisplayName(game)} · ${progressLabel(game)}`}
      />
      <div style={{
        position: 'absolute', top: '8%', bottom: 0, left: '50%', width: 1, transform: 'translateX(-50%)',
        background: `linear-gradient(180deg, transparent, ${THEME.p2}, transparent)`,
        opacity: 0.6,
      }} />
      <PlayerHalf
        side="left" playerId={1} pose={snapshot.players.p1}
        width={halfW} height={fullH}
        foreground={gameForeground(game, 'left', halfW, fullH)}
        cornerLabel={p1CornerLabel(game)}
      />
      <PlayerHalf
        side="right" playerId={2} pose={snapshot.players.p2}
        width={halfW} height={fullH}
        foreground={gameForeground(game, 'right', halfW, fullH)}
        cornerLabel={p2CornerLabel(game)}
      />
    </div>
  )
}
