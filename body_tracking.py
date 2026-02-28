import cv2
from ultralytics import YOLO
import numpy as np

# ---------------- CONFIG ----------------
INPUT_MP4 = r"C:\Users\ryuy1\henshack2026\WIN_20260228_14_32_19_Pro.mp4"
CONF_THRES = 0.5
EMA_ALPHA = 0.2
RATIO_DEADZONE = 0.06
FLIP_SELFIE = True              
# ---------------------------------------

# Load YOLO pose model
model = YOLO("yolov8n-pose.pt")

# Open video file
cap = cv2.VideoCapture(INPUT_MP4)
if not cap.isOpened():
    raise RuntimeError(f"Error: Could not open video file: {INPUT_MP4}")

# COCO keypoint indices (YOLOv8 pose order)
IDX = {
    "r_shoulder": 5, "l_shoulder": 6,
    "r_elbow": 7,    "l_elbow": 8,
    "r_wrist": 9,    "l_wrist": 10,
    "r_hip": 11,     "l_hip": 12,
    "r_knee": 13,    "l_knee": 14,
    "r_ankle": 15,   "l_ankle": 16,
}

def angle_abc(a, b, c):
    """Angle at point b formed by a-b-c, in degrees."""
    ba = a - b
    bc = c - b
    denom = (np.linalg.norm(ba) * np.linalg.norm(bc))
    if denom < 1e-6:
        return np.nan
    cosang = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosang)))

def dist(a, b):
    return float(np.linalg.norm(a - b))

# Output per-frame angles:
# columns = [shoulder-hip-knee, hip-hip-knee, hip-knee-ankle]
angles_per_frame = []

# Optional: also keep which side was used: -1=RIGHT, +1=LEFT, 0=CENTER/unknown
side_per_frame = []

ema_diff = 0.0

frame_idx = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break

    if FLIP_SELFIE:
        frame = cv2.flip(frame, 1)

    # Run pose inference
    r = model(frame, verbose=False)[0]

    # Default if no usable pose/person this frame
    ang_triplet = [np.nan, np.nan, np.nan]
    side_code = 0

    if r.keypoints is not None:
        kpts_xy_all = r.keypoints.xy.cpu().numpy()      # (people, 17, 2)
        kpts_cf_all = r.keypoints.conf.cpu().numpy()    # (people, 17)

        # Choose ONE person (largest bbox area if boxes exist, else first person)
        p = 0
        if getattr(r, "boxes", None) is not None and r.boxes is not None and len(r.boxes) > 0:
            # pick person with largest area
            xyxy = r.boxes.xyxy.cpu().numpy()  # (people,4)
            areas = (xyxy[:, 2] - xyxy[:, 0]) * (xyxy[:, 3] - xyxy[:, 1])
            p = int(np.argmax(areas))

        kpts_xy = kpts_xy_all[p]   # (17,2)
        kpts_cf = kpts_cf_all[p]   # (17,)

        def seg_len(i, j):
            if kpts_cf[i] > CONF_THRES and kpts_cf[j] > CONF_THRES:
                return dist(kpts_xy[i], kpts_xy[j])
            return None

        # Closer-side estimate using pixel lengths (upper arm + thigh)
        left_upper_arm  = seg_len(IDX["l_shoulder"], IDX["l_elbow"])
        right_upper_arm = seg_len(IDX["r_shoulder"], IDX["r_elbow"])
        left_thigh      = seg_len(IDX["l_hip"], IDX["l_knee"])
        right_thigh     = seg_len(IDX["r_hip"], IDX["r_knee"])

        left_segs  = [v for v in (left_upper_arm, left_thigh) if v is not None]
        right_segs = [v for v in (right_upper_arm, right_thigh) if v is not None]

        closest_side = None
        if left_segs and right_segs:
            left_scale = float(np.mean(left_segs))
            right_scale = float(np.mean(right_segs))

            ratio_diff = (left_scale - right_scale) / max(left_scale, right_scale)
            ema_diff = (1 - EMA_ALPHA) * ema_diff + EMA_ALPHA * ratio_diff

            if abs(ema_diff) < RATIO_DEADZONE:
                closest_side = None
                side_code = 0
            elif ema_diff > 0:
                closest_side = "left"
                side_code = +1
            else:
                closest_side = "right"
                side_code = -1

        def get_pt(name):
            i = IDX[name]
            if kpts_cf[i] > CONF_THRES:
                return kpts_xy[i].astype(np.float32)
            return None

        # Compute angles on the chosen side (if we have one)
        if closest_side is not None:
            side_prefix = "l_" if closest_side == "left" else "r_"
            other_prefix = "r_" if closest_side == "left" else "l_"

            shoulder  = get_pt(side_prefix + "shoulder")
            hip       = get_pt(side_prefix + "hip")
            knee      = get_pt(side_prefix + "knee")
            ankle     = get_pt(side_prefix + "ankle")
            other_hip = get_pt(other_prefix + "hip")

            # 1) shoulder, hip, knee (angle at HIP)
            ang1 = np.nan
            if shoulder is not None and hip is not None and knee is not None:
                ang1 = angle_abc(shoulder, hip, knee)

            # 2) hip, hip, knee (OTHER hip -> chosen hip -> chosen knee; angle at chosen HIP)
            ang2 = np.nan
            if other_hip is not None and hip is not None and knee is not None:
                ang2 = angle_abc(other_hip, hip, knee)

            # 3) hip, knee, ankle (angle at KNEE)
            ang3 = np.nan
            if hip is not None and knee is not None and ankle is not None:
                ang3 = angle_abc(hip, knee, ankle)

            ang_triplet = [ang1, ang2, ang3]

    angles_per_frame.append(ang_triplet)
    side_per_frame.append(side_code)

    frame_idx += 1

cap.release()

angles_np = np.asarray(angles_per_frame, dtype=np.float32)  # shape (num_frames, 3)
side_np = np.asarray(side_per_frame, dtype=np.int8)         # shape (num_frames,)

print("angles_np shape:", angles_np.shape)
print("side_np shape:", side_np.shape)

# If you want to save them:
# np.save("angles.npy", angles_np)
# np.save("side.npy", side_np)

# angles_np is your numpy array output (per-frame angles)
# columns: [shoulder-hip-knee, hip-hip-knee, hip-knee-ankle]
