import type { SessionSnapshot } from '../types'
import { GestureRing } from '../components/GestureRing'
import { THEME, playerColor } from '../theme'

interface Props { snapshot: SessionSnapshot }

export function LeaderboardScreen({ snapshot }: Props) {
  const data = snapshot.leaderboard
  if (!data) return null
  const winnerId = data.winner
  const winnerLabel = winnerId == null ? 'DRAW' : `PLAYER ${winnerId}`
  const winnerColor = winnerId == null ? THEME.accent : playerColor(winnerId as 1 | 2)

  return (
    <div style={{
      position: 'absolute', inset: 0,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap: 32, padding: '4vh 4vw',
    }}>
      <div style={{
        fontFamily: THEME.fontMono, fontSize: 16, color: THEME.dim, letterSpacing: '0.3em',
      }}>
        FINAL · {data.p1_wins} vs {data.p2_wins}
      </div>
      <div style={{
        fontFamily: THEME.fontDisplay, fontSize: '7vw',
        color: winnerColor,
        textShadow: `0 0 36px ${winnerColor}`,
      }}>
        {winnerLabel} WINS
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '2fr 1fr 1fr 1fr',
        rowGap: 12, columnGap: 24,
        fontFamily: THEME.fontMono, fontSize: 22,
        marginTop: 24,
        minWidth: '60vw',
      }}>
        <div style={{ color: THEME.dim, fontSize: 12, letterSpacing: '0.2em' }}>GAME</div>
        <div style={{ color: THEME.p1, fontSize: 12, letterSpacing: '0.2em' }}>P1</div>
        <div style={{ color: THEME.p2, fontSize: 12, letterSpacing: '0.2em' }}>P2</div>
        <div style={{ color: THEME.accent, fontSize: 12, letterSpacing: '0.2em' }}>WINNER</div>

        {data.games.map((g, i) => (
          <RowGroup key={i} g={g} />
        ))}
      </div>

      <GestureRing
        progress={snapshot.gesture_progress}
        size={180}
        label="HANDS UP TO PLAY AGAIN"
      />
    </div>
  )
}

interface GameSummary {
  name: string
  p1_metric: number | string | null
  p2_metric: number | string | null
  metric_unit: string
  winner: 1 | 2 | null
}

function RowGroup({ g }: { g: GameSummary }) {
  const winnerColor = g.winner == null ? THEME.accent : playerColor(g.winner as 1 | 2)
  return (
    <>
      <div style={{ color: THEME.text }}>{g.name}</div>
      <div style={{ color: THEME.p1, textShadow: THEME.glowP1, fontVariantNumeric: 'tabular-nums' }}>
        {g.p1_metric ?? '—'}<span style={{ fontSize: 12, opacity: 0.6, marginLeft: 6 }}>{g.metric_unit}</span>
      </div>
      <div style={{ color: THEME.p2, textShadow: THEME.glowP2, fontVariantNumeric: 'tabular-nums' }}>
        {g.p2_metric ?? '—'}<span style={{ fontSize: 12, opacity: 0.6, marginLeft: 6 }}>{g.metric_unit}</span>
      </div>
      <div style={{ color: winnerColor, textShadow: `0 0 8px ${winnerColor}`, fontWeight: 700 }}>
        {g.winner == null ? 'DRAW' : `P${g.winner}`}
      </div>
    </>
  )
}
