export type Keypoint = [number, number, number]  // [x, y, conf] in 0..1 normalized

export interface Pose {
  keypoints: Keypoint[]
  bbox: [number, number, number, number]
  score: number
}

export type Screen = 'title' | 'countdown' | 'game' | 'intermission' | 'leaderboard'

// ---- Touch the Circle ----

export interface Target {
  x: number
  y: number
  radius: number
}

export interface TouchCircleRoundResult {
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
  results: TouchCircleRoundResult[]
}

// ---- Goalie ----

export interface GoalieShotResult {
  zone: number
  p1_saved: boolean
  p2_saved: boolean
  p1_save_time_ms: number | null
  p2_save_time_ms: number | null
}

export interface GoalieBall {
  zone: number
  spawned_at_ms: number
  travel_ms: number
}

export type Zone = [number, number, number, number]  // [xmin, ymin, xmax, ymax] half-screen normalized

export interface GoalieState {
  type: 'goalie'
  shot: number
  total_shots: number
  phase: 'preroll' | 'active' | 'done'
  ball: GoalieBall | null
  zones: Zone[]
  results: GoalieShotResult[]
}

// ---- Union ----

export type GameState = TouchCircleState | GoalieState

// Backwards-compat alias for components that haven't been updated yet
export type RoundResult = TouchCircleRoundResult

// ---- Session-level shapes ----

export interface GameSummary {
  name: string
  p1_metric: number | string | null
  p2_metric: number | string | null
  metric_unit: string
  winner: 1 | 2 | null
}

export interface IntermissionData {
  last_summary: GameSummary | null
  next_game_name: string | null
  current_index: number  // 1-based for display ("Game 2 of 4 starting…")
  total_games: number
  remaining_ms: number
}

export interface LeaderboardData {
  winner: 1 | 2 | null
  p1_wins: number
  p2_wins: number
  games: GameSummary[]
}

export interface SessionSnapshot {
  screen: Screen
  gesture_progress: number
  countdown_remaining_ms?: number
  countdown_ms_total?: number
  game?: GameState
  intermission?: IntermissionData
  leaderboard?: LeaderboardData
  players: { p1: Pose | null; p2: Pose | null }
}

export interface Config {
  touch_circle: {
    rounds: number
    preroll_ms_min: number
    preroll_ms_max: number
    target_size_pct: number
    summary_min_hold_ms?: number
  }
  goalie: {
    shots: number
    preroll_ms_min: number
    preroll_ms_max: number
    ball_travel_ms: number
  }
  gesture: { hold_ms: number; idle_timeout_s: number }
  session: { intermission_ms: number }
}
