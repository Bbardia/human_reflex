import { useSessionState } from './ws'
import { TitleScreen } from './screens/TitleScreen'
import { CountdownScreen } from './screens/CountdownScreen'
import { GameScreen } from './screens/GameScreen'
import { SummaryScreen } from './screens/SummaryScreen'
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
    <div style={{ position: 'absolute', inset: 0, background: THEME.bgGradient, overflow: 'hidden' }}>
      {snapshot.screen === 'title' && <TitleScreen snapshot={snapshot} />}
      {snapshot.screen === 'countdown' && <CountdownScreen snapshot={snapshot} />}
      {snapshot.screen === 'game' && <GameScreen snapshot={snapshot} />}
      {snapshot.screen === 'summary' && <SummaryScreen snapshot={snapshot} />}
    </div>
  )
}
