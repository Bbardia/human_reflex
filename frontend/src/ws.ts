import { useEffect, useState } from 'react'
import type { Config, SessionSnapshot } from './types'

interface UseSessionState {
  config: Config | null
  snapshot: SessionSnapshot | null
  connected: boolean
}

export function useSessionState(): UseSessionState {
  const [config, setConfig] = useState<Config | null>(null)
  const [snapshot, setSnapshot] = useState<SessionSnapshot | null>(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${proto}//${window.location.host}/ws`
    let ws: WebSocket | null = null
    let reconnectTimer: number | null = null

    const connect = () => {
      ws = new WebSocket(url)
      ws.onopen = () => setConnected(true)
      ws.onclose = () => {
        setConnected(false)
        reconnectTimer = window.setTimeout(connect, 1000)
      }
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.type === 'config') setConfig(msg.data as Config)
          else if (msg.type === 'state') setSnapshot(msg.data as SessionSnapshot)
        } catch (err) {
          console.error('bad ws msg', err)
        }
      }
    }
    connect()

    return () => {
      if (reconnectTimer) window.clearTimeout(reconnectTimer)
      ws?.close()
    }
  }, [])

  return { config, snapshot, connected }
}
