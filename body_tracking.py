import cv2
from ultralytics import YOLO
import math

# Load a YOLO pose model (not the regular detection model)
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

while True:
    ret, frame = stream.read()
    if not ret:
        print("Error loading video")
        break

    frame = cv2.flip(frame, 1)

    # Run pose inference
    r = model(frame, verbose=False)[0]

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
                    # comment this out if labels are too cluttered
                    cv2.putText(frame, name, (int(x) + 5, int(y) - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

    cv2.imshow("Webcam (Pose)", frame)
    if cv2.waitKey(1) == ord('q'):
        break

stream.release()
cv2.destroyAllWindows()
