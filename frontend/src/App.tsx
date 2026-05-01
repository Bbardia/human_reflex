import { useSessionState } from './ws'
import { TitleScreen } from './screens/TitleScreen'
import { CountdownScreen } from './screens/CountdownScreen'
import { GameScreen } from './screens/GameScreen'
import { IntermissionScreen } from './screens/IntermissionScreen'
import { LeaderboardScreen } from './screens/LeaderboardScreen'
import { CameraStream } from './components/CameraStream'
import { THEME } from './theme'

export default function App() {
  const { snapshot, connected } = useSessionState()

  if (!snapshot) {
    return (
      <div style={{
        position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: THEME.bgGradient, color: THEME.dim, fontFamily: THEME.fontMono,
      }}>
        {connected ? 'Loading session…' : 'Connecting to backend…'}
      </div>
    )
  }

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', background: '#000' }}>
      <CameraStream />
      <div style={{
        position: 'absolute', inset: 0, zIndex: 1, pointerEvents: 'none',
        background: 'linear-gradient(180deg, rgba(10,0,26,0.55) 0%, rgba(26,0,64,0.55) 100%)',
      }} />
      <div style={{ position: 'absolute', inset: 0, zIndex: 2 }}>
        {snapshot.screen === 'title' && <TitleScreen snapshot={snapshot} />}
        {snapshot.screen === 'countdown' && <CountdownScreen snapshot={snapshot} />}
        {snapshot.screen === 'game' && <GameScreen snapshot={snapshot} />}
        {snapshot.screen === 'intermission' && <IntermissionScreen snapshot={snapshot} />}
        {snapshot.screen === 'leaderboard' && <LeaderboardScreen snapshot={snapshot} />}
      </div>
    </div>
  )
}
