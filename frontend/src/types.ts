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

// ---- Pose Simon ----

export type PoseSimonPose = 'arms_up' | 't_pose' | 'left_arm_up' | 'right_arm_up' | 'hands_on_hips' | 'squat'

export interface PoseSimonState {
  type: 'pose_simon'
  round: number
  phase: 'demo' | 'input' | 'resolve' | 'done'
  sequence: PoseSimonPose[]
  p1_index: number
  p2_index: number
  p1_completed: boolean
  p2_completed: boolean
  rounds_cleared_p1: number
  rounds_cleared_p2: number
}

// ---- Laser Limbo ----

export interface LaserDescriptor {
  spawn_ms: number
  duration_ms: number
  orientation: 'h' | 'v'
  direction: 1 | -1
  thickness: number
}

export interface LaserLimboState {
  type: 'laser_limbo'
  phase: 'active' | 'resolve' | 'done'
  match_duration_ms: number
  p1_hp: number
  p2_hp: number
  p1_hits: number
  p2_hits: number
  starting_hp: number
  lasers: LaserDescriptor[]
}

// ---- Union ----

export type GameState = TouchCircleState | GoalieState | PoseSimonState | LaserLimboState

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
  is_sudden_death?: boolean
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
  pose_simon: {
    starting_sequence_length: number
    demo_pose_ms: number
    demo_gap_ms: number
    hold_ms: number
    timeout_per_pose_ms: number
  }
  laser_limbo: {
    match_duration_s: number
    starting_hp: number
    rate_hz_early: number
    rate_hz_late: number
    ramp_at_s: number
    laser_duration_ms: number
    laser_thickness: number
    invuln_ms: number
  }
  gesture: { hold_ms: number; idle_timeout_s: number }
  session: { intermission_ms: number }
}
