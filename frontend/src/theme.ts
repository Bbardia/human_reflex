export const THEME = {
  bgGradient: 'linear-gradient(180deg, #0a001a 0%, #1a0040 100%)',
  p1: '#00ffff',
  p2: '#ff00aa',
  target: '#ff006e',
  accent: '#ffff00',
  text: '#ffffff',
  dim: 'rgba(255,255,255,0.6)',
  glowP1: '0 0 12px #00ffff',
  glowP2: '0 0 12px #ff00aa',
  glowTarget: '0 0 18px #ff006e',
  fontDisplay: "'Audiowide', system-ui, sans-serif",
  fontMono: "'JetBrains Mono', 'Courier New', monospace",
}

export type PlayerId = 1 | 2
export const playerColor = (id: PlayerId) => (id === 1 ? THEME.p1 : THEME.p2)
export const playerGlow = (id: PlayerId) => (id === 1 ? THEME.glowP1 : THEME.glowP2)
