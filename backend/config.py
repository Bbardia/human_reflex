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
    server: ServerConfig = field(default_factory=ServerConfig)


CONFIG = Config()


def public_config_dict() -> dict:
    """Subset of config that gets shipped to the frontend on connect."""
    return {
        "touch_circle": asdict(CONFIG.touch_circle),
        "gesture": asdict(CONFIG.gesture),
    }
