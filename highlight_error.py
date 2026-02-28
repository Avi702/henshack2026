# visualize_error_overlay.py
# Overlay a per-joint (or per-bone) error array onto an MP4 as a colored skeleton heatmap.
#
# Supports:
#   A) You already saved keypoints per frame:
#        kpts_xy.npy  shape (T,17,2)  float32  (pixel coords)
#        kpts_cf.npy  shape (T,17)    float32  (confidence)
#      and you have:
#        err.npy      shape (T,17) OR (T,17,2) OR (T,B)  (see below)
#
#   B) You only have err.npy and want to re-run YOLO pose to get keypoints for drawing:
#        --use-yolo (needs ultralytics + yolov8n-pose.pt)
#
# Error array formats:
#   - (T,17): per-joint scalar error
#   - (T,17,2): per-joint vector error; magnitude is used
#   - (T,B): per-bone error, where B matches the number of skeleton edges defined below (len(EDGES))
#
# Output:
#   Writes an MP4 with colored joints/bones (hotter color = higher error)

import argparse
import os
import cv2
import numpy as np

# ---------------- Skeleton definition (COCO 17) ----------------
# YOLOv8 pose keypoint order is COCO:
# 0:nose,1:l_eye,2:r_eye,3:l_ear,4:r_ear,5:l_shoulder,6:r_shoulder,
# 7:l_elbow,8:r_elbow,9:l_wrist,10:r_wrist,11:l_hip,12:r_hip,
# 13:l_knee,14:r_knee,15:l_ankle,16:r_ankle

EDGES = [
    (5, 7),  (7, 9),   # left arm
    (6, 8),  (8, 10),  # right arm
    (11, 13), (13, 15),# left leg
    (12, 14), (14, 16),# right leg
    (5, 6),            # shoulders
    (11, 12),          # hips
    (5, 11),           # left torso
    (6, 12),           # right torso
    (0, 5), (0, 6),    # head to shoulders (approx)
]

# ---------------- Utility ----------------
def safe_norm(v, axis=-1):
    n = np.linalg.norm(v, axis=axis)
    n[np.isnan(n)] = np.nan
    return n

def normalize_err(err_frame, clip_max):
    """
    Map err values (float) to 0..255 uint8 using clip_max.
    NaNs map to 0 (and can be skipped in drawing).
    """
    e = err_frame.astype(np.float32)
    out = np.zeros_like(e, dtype=np.uint8)
    mask = np.isfinite(e)
    if not np.any(mask):
        return out, mask
    e2 = np.clip(e[mask], 0.0, clip_max)
    out[mask] = (255.0 * (e2 / clip_max)).astype(np.uint8)
    return out, mask

def color_from_value_u8(v_u8, colormap=cv2.COLORMAP_TURBO):
    """
    v_u8: scalar 0..255
    returns BGR tuple
    """
    # applyColorMap expects (H,W) or (H,W,1)
    arr = np.array([[v_u8]], dtype=np.uint8)
    c = cv2.applyColorMap(arr, colormap)[0, 0]  # BGR
    return int(c[0]), int(c[1]), int(c[2])

def draw_skeleton_heat(
    frame,
    kpts_xy,       # (17,2)
    kpts_cf,       # (17,)
    joint_u8=None, # (17,) uint8, optional
    bone_u8=None,  # (B,)  uint8, optional
    conf_thres=0.5,
    joint_radius=5,
    line_thickness=4,
    draw_joints=True,
    draw_bones=True,
    show_values=False
):
    """
    Draw joints and edges colored by error intensity.
    If both joint_u8 and bone_u8 are provided, bones use bone_u8 and joints use joint_u8.
    If only joint_u8 is provided, bones use average(joint endpoints).
    """
    h, w = frame.shape[:2]

    # bones
    if draw_bones:
        for bi, (i, j) in enumerate(EDGES):
            if kpts_cf[i] < conf_thres or kpts_cf[j] < conf_thres:
                continue
            xi, yi = kpts_xy[i]
            xj, yj = kpts_xy[j]
            if not (np.isfinite(xi) and np.isfinite(yi) and np.isfinite(xj) and np.isfinite(yj)):
                continue

            if bone_u8 is not None and bi < len(bone_u8):
                v = int(bone_u8[bi])
            elif joint_u8 is not None:
                v = int((int(joint_u8[i]) + int(joint_u8[j])) / 2)
            else:
                v = 0

            color = color_from_value_u8(v)
            cv2.line(frame, (int(xi), int(yi)), (int(xj), int(yj)), color, line_thickness, cv2.LINE_AA)

    # joints
    if draw_joints and joint_u8 is not None:
        for i in range(17):
            if kpts_cf[i] < conf_thres:
                continue
            x, y = kpts_xy[i]
            if not (np.isfinite(x) and np.isfinite(y)):
                continue
            v = int(joint_u8[i])
            color = color_from_value_u8(v)
            cv2.circle(frame, (int(x), int(y)), joint_radius, color, -1, cv2.LINE_AA)

            if show_values:
                cv2.putText(
                    frame, f"{v}",
                    (int(x) + 6, int(y) - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA
                )

    return frame

# ---------------- Main ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp4", required=True, help="Input MP4 path")
    ap.add_argument("--err", required=True, help="Path to error .npy (T,17) or (T,17,2) or (T,B)")
    ap.add_argument("--out", default="error_overlay.mp4", help="Output MP4 path")

    ap.add_argument("--kpts-xy", default=None, help="Optional: keypoints xy .npy (T,17,2)")
    ap.add_argument("--kpts-cf", default=None, help="Optional: keypoints conf .npy (T,17)")

    ap.add_argument("--use-yolo", action="store_true",
                    help="If set, run YOLO pose to get keypoints instead of loading kpts .npy")
    ap.add_argument("--yolo-model", default="yolov8n-pose.pt", help="YOLO pose model path")

    ap.add_argument("--conf-thres", type=float, default=0.5, help="Keypoint conf threshold for drawing")
    ap.add_argument("--clip-max", type=float, default=None,
                    help="Max error value mapped to hottest color. If omitted, uses 95th percentile.")
    ap.add_argument("--show-values", action="store_true", help="Draw 0..255 intensity numbers at joints")

    ap.add_argument("--draw-joints", action="store_true", help="Draw joint circles")
    ap.add_argument("--draw-bones", action="store_true", help="Draw bones/edges")
    ap.add_argument("--joint-radius", type=int, default=5)
    ap.add_argument("--line-thickness", type=int, default=4)

    args = ap.parse_args()

    if not args.draw_joints and not args.draw_bones:
        # default: draw both if neither explicitly requested
        args.draw_joints = True
        args.draw_bones = True

    err = np.load(args.err)
    if err.ndim == 3 and err.shape[1:] == (17, 2):
        # vector error -> magnitude
        err_scalar = safe_norm(err, axis=-1)  # (T,17)
        err_is_joint = True
        err_is_bone = False
    elif err.ndim == 2 and err.shape[1] == 17:
        err_scalar = err.astype(np.float32)   # (T,17)
        err_is_joint = True
        err_is_bone = False
    elif err.ndim == 2 and err.shape[1] == len(EDGES):
        err_scalar = err.astype(np.float32)   # (T,B)
        err_is_joint = False
        err_is_bone = True
    else:
        raise ValueError(
            f"Unsupported err shape {err.shape}. Expected (T,17), (T,17,2), or (T,{len(EDGES)})."
        )

    # Open video
    cap = cv2.VideoCapture(args.mp4)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {args.mp4}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Decide T we will process
    T = err_scalar.shape[0]
    T_proc = min(total_frames if total_frames > 0 else T, T)

    # Load or compute keypoints
    kpts_xy_all = None
    kpts_cf_all = None

    yolo_model = None
    if args.use_yolo:
        from ultralytics import YOLO
        yolo_model = YOLO(args.yolo_model)
    else:
        if args.kpts_xy is None or args.kpts_cf is None:
            raise ValueError("Provide --kpts-xy and --kpts-cf OR use --use-yolo.")
        kpts_xy_all = np.load(args.kpts_xy).astype(np.float32)
        kpts_cf_all = np.load(args.kpts_cf).astype(np.float32)
        if kpts_xy_all.shape[:2] != (T, 17) or kpts_xy_all.shape[2] != 2:
            raise ValueError(f"kpts_xy shape must be (T,17,2). Got {kpts_xy_all.shape}")
        if kpts_cf_all.shape != (T, 17):
            raise ValueError(f"kpts_cf shape must be (T,17). Got {kpts_cf_all.shape}")

    # Choose clip-max for colormap scaling
    if args.clip_max is None:
        finite_vals = err_scalar[np.isfinite(err_scalar)]
        clip_max = float(np.percentile(finite_vals, 95)) if finite_vals.size else 1.0
        clip_max = max(clip_max, 1e-6)
    else:
        clip_max = float(args.clip_max)
        clip_max = max(clip_max, 1e-6)

    # Prepare writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    writer = cv2.VideoWriter(args.out, fourcc, fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError(f"Could not open VideoWriter for: {args.out}")

    frame_idx = 0
    while frame_idx < T_proc:
        ret, frame = cap.read()
        if not ret:
            break

        # Get keypoints for this frame
        if args.use_yolo:
            r = yolo_model(frame, verbose=False)[0]
            if r.keypoints is None:
                # no pose detected: still write original frame with a label
                cv2.putText(frame, "NO POSE", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA)
                writer.write(frame)
                frame_idx += 1
                continue

            kpts_xy_all_people = r.keypoints.xy.cpu().numpy()   # (people,17,2)
            kpts_cf_all_people = r.keypoints.conf.cpu().numpy() # (people,17)

            # pick largest bbox area if available else first
            p = 0
            if getattr(r, "boxes", None) is not None and r.boxes is not None and len(r.boxes) > 0:
                xyxy = r.boxes.xyxy.cpu().numpy()
                areas = (xyxy[:, 2] - xyxy[:, 0]) * (xyxy[:, 3] - xyxy[:, 1])
                p = int(np.argmax(areas))

            kpts_xy = kpts_xy_all_people[p].astype(np.float32)
            kpts_cf = kpts_cf_all_people[p].astype(np.float32)
        else:
            kpts_xy = kpts_xy_all[frame_idx]
            kpts_cf = kpts_cf_all[frame_idx]

        # Get errors for this frame and map to 0..255
        if err_is_joint:
            joint_u8, joint_mask = normalize_err(err_scalar[frame_idx], clip_max)
            bone_u8 = None
        else:
            # bone errors
            bone_u8, bone_mask = normalize_err(err_scalar[frame_idx], clip_max)
            joint_u8 = None

        # Draw
        frame = draw_skeleton_heat(
            frame,
            kpts_xy=kpts_xy,
            kpts_cf=kpts_cf,
            joint_u8=joint_u8,
            bone_u8=bone_u8,
            conf_thres=args.conf_thres,
            joint_radius=args.joint_radius,
            line_thickness=args.line_thickness,
            draw_joints=args.draw_joints,
            draw_bones=args.draw_bones,
            show_values=args.show_values
        )

        # Legend
        cv2.putText(
            frame,
            f"Error heat: 0 .. {clip_max:.3g} (clipped @95% if auto)",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        writer.write(frame)
        frame_idx += 1

    cap.release()
    writer.release()
    print(f"Saved overlay video: {args.out}")

if __name__ == "__main__":
    main()