export type Keypoint = [number, number, number]  // [x, y, conf] in 0..1 normalized

export interface Pose {
  keypoints: Keypoint[]
  bbox: [number, number, number, number]
  score: number
}

export type Screen = 'title' | 'countdown' | 'game' | 'summary'

export interface Target {
  x: number
  y: number
  radius: number
}

export interface RoundResult {
  p1_time_ms: number | null
  p2_time_ms: number | null
  p1_false_start: boolean
  p2_false_start: boolean
}

export interface TouchCircleState {
  type: 'touch_circle'
  round: number
  total_rounds: number
  phase: 'preroll' | 'active' | 'done'
  target: Target | null
  results: RoundResult[]
}

export interface SessionSnapshot {
  screen: Screen
  gesture_progress: number
  countdown_remaining_ms?: number
  countdown_ms_total?: number
  game?: TouchCircleState
  summary?: {
    name: string
    p1_metric: number | null
    p2_metric: number | null
    metric_unit: string
    winner: 1 | 2 | null
  }
  players: { p1: Pose | null; p2: Pose | null }
}

export interface Config {
  touch_circle: {
    rounds: number
    preroll_ms_min: number
    preroll_ms_max: number
    target_size_pct: number
    summary_hold_ms: number
  }
  gesture: { hold_ms: number; idle_timeout_s: number }
}
