import cv2
from ultralytics import YOLO
import math
import numpy as np

model = YOLO("yolov8n-pose.pt")

stream = cv2.VideoCapture(0)
lift_type = None

if not stream.isOpened():
    print("Error: No Video")
    exit()

# COCO 17 keypoints names (YOLOv8 pose uses this order)
COCO_KPTS = [
    "nose","right_eye","left_eye","right_ear","left_ear",
    "right_shoulder","left_shoulder","right_elbow","left_elbow",
    "right_wrist","left_wrist","right_hip","left_hip",
    "right_knee","left_knee","right_ankle","left_ankle"
]

# COCO skeleton connections (pairs of keypoint indices)
SKELETON = [
    (5, 7), (7, 9),        # left arm
    (6, 8), (8, 10),       # right arm
    (5, 6),                # shoulders
    (5, 11), (6, 12),      # torso
    (11, 12),              # hips
    (11, 13), (13, 15),    # left leg
    (12, 14), (14, 16),    # right leg
    (0, 1), (0, 2),        # nose to eyes
    (1, 3), (2, 4)         # eyes to ears
]

CONF_THRES = 0.5  # keypoint confidence threshold

# Indices (remember: COCO_KPTS list above has "right_*" before "left_*" for many joints)
IDX = {
    "r_shoulder": 5, "l_shoulder": 6,
    "r_elbow": 7,    "l_elbow": 8,
    "r_wrist": 9,    "l_wrist": 10,
    "r_hip": 11,     "l_hip": 12,
    "r_knee": 13,    "l_knee": 14,
    "r_ankle": 15,   "l_ankle": 16,
}

def dist(a, b):
    return float(np.linalg.norm(a - b))

# Simple smoothing to avoid flicker
ema_diff = 0.0
EMA_ALPHA = 0.2  # 0..1 (higher = more responsive)
RATIO_DEADZONE = 0.06  # ~6% difference => call it "CENTER"

while True:
    ret, frame = stream.read()
    if not ret:
        print("Error loading video")
        break

    frame = cv2.flip(frame, 1)

    # Run pose inference
    r = model(frame, verbose=False)[0]

    closest_text = None

    # If pose keypoints exist, draw them
    if r.keypoints is not None:
        kpts_xy = r.keypoints.xy.cpu().numpy()      # (people, 17, 2)
        kpts_cf = r.keypoints.conf.cpu().numpy()    # (people, 17)

        for p in range(kpts_xy.shape[0]):  # each person
            # Draw skeleton lines
            for a, b in SKELETON:
                if kpts_cf[p, a] > CONF_THRES and kpts_cf[p, b] > CONF_THRES:
                    ax, ay = kpts_xy[p, a]
                    bx, by = kpts_xy[p, b]
                    cv2.line(frame, (int(ax), int(ay)), (int(bx), int(by)), (0, 255, 0), 2)

            # Draw keypoint dots (and optionally labels)
            for j, name in enumerate(COCO_KPTS):
                if kpts_cf[p, j] > CONF_THRES:
                    x, y = kpts_xy[p, j]
                    cv2.circle(frame, (int(x), int(y)), 4, (0, 0, 255), -1)
                    cv2.putText(frame, name, (int(x) + 5, int(y) - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

            # --------- LEFT vs RIGHT "CLOSER" ESTIMATE ----------
            # Use pixel lengths as a proxy for closeness (bigger == closer).
            # We'll average two segments per side: upper-arm and thigh (more stable than wrists/ankles alone).

            def seg_len(i, j):
                if kpts_cf[p, i] > CONF_THRES and kpts_cf[p, j] > CONF_THRES:
                    return dist(kpts_xy[p, i], kpts_xy[p, j])
                return None

            left_upper_arm = seg_len(IDX["l_shoulder"], IDX["l_elbow"])
            right_upper_arm = seg_len(IDX["r_shoulder"], IDX["r_elbow"])
            left_thigh = seg_len(IDX["l_hip"], IDX["l_knee"])
            right_thigh = seg_len(IDX["r_hip"], IDX["r_knee"])

            left_segs = [v for v in [left_upper_arm, left_thigh] if v is not None]
            right_segs = [v for v in [right_upper_arm, right_thigh] if v is not None]

            if left_segs and right_segs:
                left_scale = float(np.mean(left_segs))
                right_scale = float(np.mean(right_segs))

                # ratio diff in [-1, 1] roughly
                ratio_diff = (left_scale - right_scale) / max(left_scale, right_scale)

                # smooth it
                ema_diff = (1 - EMA_ALPHA) * ema_diff + EMA_ALPHA * ratio_diff

                if abs(ema_diff) < RATIO_DEADZONE:
                    closest_text = "CENTER"
                elif ema_diff > 0:
                    closest_text = "LEFT CLOSER"
                else:
                    closest_text = "RIGHT CLOSER"

                # optional: show debug numbers
                cv2.putText(frame, f"L:{left_scale:.1f}  R:{right_scale:.1f}  d:{ema_diff:+.3f}",
                            (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # If you only care about one person, break after first
            # break

    if closest_text:
        cv2.putText(frame, closest_text, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imshow("Webcam (Pose)", frame)
    if cv2.waitKey(1) == ord('q'):
        break

stream.release()
cv2.destroyAllWindows()
