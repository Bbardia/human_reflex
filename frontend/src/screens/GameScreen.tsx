import { useEffect, useState } from 'react'
import type { SessionSnapshot } from '../types'
import { PlayerHalf } from '../components/PlayerHalf'
import { StatusBar } from '../components/StatusBar'
import { TouchCircleCanvas } from '../games/TouchCircleCanvas'
import { THEME } from '../theme'

interface Props { snapshot: SessionSnapshot }

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
  const last = game.results[game.results.length - 1]

  return (
    <div style={{
      position: 'absolute', inset: 0,
    }}>
      <StatusBar
        center={`${game.type === 'touch_circle' ? 'TOUCH THE CIRCLE' : ''} · ROUND ${game.round} / ${game.total_rounds}`}
      />
      <div style={{
        position: 'absolute', top: '8%', bottom: 0, left: '50%', width: 1, transform: 'translateX(-50%)',
        background: `linear-gradient(180deg, transparent, ${THEME.p2}, transparent)`,
        opacity: 0.6,
      }} />
      <PlayerHalf
        side="left" playerId={1} pose={snapshot.players.p1}
        width={halfW} height={fullH}
        foreground={<TouchCircleCanvas state={game} side="left" width={halfW} height={fullH} />}
        cornerLabel={last?.p1_time_ms != null ? `${last.p1_time_ms}` : ''}
      />
      <PlayerHalf
        side="right" playerId={2} pose={snapshot.players.p2}
        width={halfW} height={fullH}
        foreground={<TouchCircleCanvas state={game} side="right" width={halfW} height={fullH} />}
        cornerLabel={last?.p2_time_ms != null ? `${last.p2_time_ms}` : ''}
      />
    </div>
  )
}
