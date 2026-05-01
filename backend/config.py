"""All tunable parameters live here. The frontend receives the relevant subset
on WebSocket connect so we don't hard-code numbers in two places."""
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass(frozen=True)
class CameraConfig:
    device_index: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 60


@dataclass(frozen=True)
class PoseConfig:
    model_dir: Path = Path("backend/pose/models/yolov8n-pose_openvino_model")
    conf_threshold: float = 0.4
    iou_threshold: float = 0.5
    max_persons: int = 2


@dataclass(frozen=True)
class GestureConfig:
    hold_ms: int = 2000
    idle_timeout_s: float = 60.0


@dataclass(frozen=True)
class TouchCircleConfig:
    rounds: int = 5
    preroll_ms_min: int = 1000
    preroll_ms_max: int = 3000
    target_size_pct: float = 0.15  # of half-screen height
    false_start_speed_threshold: float = 0.5  # frame heights / sec
    false_start_min_duration_ms: int = 100
    false_start_penalty_ms: int = 2000
    summary_min_hold_ms: int = 1500  # minimum ms the summary must show before P1 can dismiss with hands-up


@dataclass(frozen=True)
class GoalieConfig:
    shots: int = 5
    preroll_ms_min: int = 1000
    preroll_ms_max: int = 3000
    ball_travel_ms: int = 700
    # 5 zones in half-screen normalized coords: (xmin, ymin, xmax, ymax)
    zones: tuple[tuple[float, float, float, float], ...] = (
        (0.05, 0.10, 0.30, 0.40),  # 0 top-left
        (0.70, 0.10, 0.95, 0.40),  # 1 top-right
        (0.375, 0.40, 0.625, 0.60),  # 2 center
        (0.05, 0.55, 0.30, 0.85),  # 3 bot-left
        (0.70, 0.55, 0.95, 0.85),  # 4 bot-right
    )
    resolve_hold_ms: int = 600  # how long to display the ball after travel completes


@dataclass(frozen=True)
class PoseSimonConfig:
    starting_sequence_length: int = 1
    demo_pose_ms: int = 600
    demo_gap_ms: int = 200
    hold_ms: int = 400  # how long a player must hold each pose for it to count
    timeout_per_pose_ms: int = 1500  # round timeout = this * sequence_length
    resolve_hold_ms: int = 1500  # how long to display the round outcome before next round
    keypoint_conf_threshold: float = 0.3
    # T-pose tolerances
    tpose_y_tolerance: float = 0.08  # |wrist.y - shoulder.y| must be within this
    tpose_x_factor: float = 1.2  # |wrist.x - shoulder.x| must exceed this * shoulder_width
    # Hands-on-hips tolerance
    hip_radius: float = 0.10  # max distance wrist↔hip in normalized coords


@dataclass(frozen=True)
class LaserLimboConfig:
    match_duration_s: float = 30.0
    starting_hp: int = 3
    rate_hz_early: float = 3.0   # Poisson rate for the first ramp_at_s seconds
    rate_hz_late: float = 5.0    # Poisson rate after ramp_at_s
    ramp_at_s: float = 15.0      # when to switch to late rate + allow vertical lasers
    laser_duration_ms: int = 800
    laser_thickness: float = 0.05  # collision threshold in normalized coords
    invuln_ms: int = 500
    resolve_hold_ms: int = 1500    # how long to display final HP / hits before is_done


@dataclass(frozen=True)
class SessionConfig:
    intermission_ms: int = 4000  # auto-advance from intermission to next countdown


@dataclass(frozen=True)
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    static_dir: Path = Path("frontend/dist")


@dataclass(frozen=True)
class Config:
    camera: CameraConfig = field(default_factory=CameraConfig)
    pose: PoseConfig = field(default_factory=PoseConfig)
    gesture: GestureConfig = field(default_factory=GestureConfig)
    touch_circle: TouchCircleConfig = field(default_factory=TouchCircleConfig)
    goalie: GoalieConfig = field(default_factory=GoalieConfig)
    pose_simon: PoseSimonConfig = field(default_factory=PoseSimonConfig)
    laser_limbo: LaserLimboConfig = field(default_factory=LaserLimboConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    server: ServerConfig = field(default_factory=ServerConfig)


CONFIG = Config()


def public_config_dict() -> dict:
    """Subset of config that gets shipped to the frontend on connect."""
    return {
        "gesture": asdict(CONFIG.gesture),
        "goalie": asdict(CONFIG.goalie),
        "laser_limbo": asdict(CONFIG.laser_limbo),
        "pose_simon": asdict(CONFIG.pose_simon),
        "session": asdict(CONFIG.session),
        "touch_circle": asdict(CONFIG.touch_circle),
    }
