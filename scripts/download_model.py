"""Downloads YOLOv8n-Pose and exports it to OpenVINO INT8 for fast Intel CPU inference."""
import sys
from pathlib import Path
from ultralytics import YOLO


def main() -> int:
    out_root = Path("backend/pose/models")
    out_root.mkdir(parents=True, exist_ok=True)

    pt_path = out_root / "yolov8n-pose.pt"
    if not pt_path.exists():
        print(f"Downloading yolov8n-pose to {pt_path}...")
        # YOLO('yolov8n-pose.pt') auto-downloads to CWD on first use; redirect by chdir
        import os
        os.chdir(out_root)
        model = YOLO("yolov8n-pose.pt")
        os.chdir(Path(__file__).resolve().parents[1])
    else:
        model = YOLO(str(pt_path))

    ov_dir = out_root / "yolov8n-pose_openvino_model"
    if ov_dir.exists():
        print(f"OpenVINO model already exported at {ov_dir}")
        return 0

    print("Exporting to OpenVINO INT8...")
    model.export(format="openvino", int8=True, imgsz=640)

    # ultralytics writes the export at the CWD. INT8 exports use the
    # `_int8_openvino_model` suffix; fp32 exports use `_openvino_model`.
    for candidate in (
        Path("yolov8n-pose_int8_openvino_model"),
        Path("yolov8n-pose_openvino_model"),
    ):
        if candidate.exists() and not ov_dir.exists():
            candidate.rename(ov_dir)
            break

    print(f"Done. Model at {ov_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
