import numpy as np
from backend.app.pipeline.features import _extract_squat, _detect_closer_side, squat_features_for_frame, _CONF_THRES

print(f"Conf threshold: {_CONF_THRES}")

def mock_pose():
    xy = np.zeros((17, 2), dtype=np.float32)
    conf = np.ones((17,), dtype=np.float32) * 0.9 # High confidence
    
    # Left side coords
    xy[6] = [100, 100] # L shoulder
    xy[8] = [100, 200] # L elbow
    xy[12] = [100, 300] # L hip
    xy[14] = [100, 400] # L knee 
    
    # Right side coords (smaller length -> further away)
    xy[5] = [200, 100] # R shoulder
    xy[7] = [200, 150] # R elbow
    xy[11] = [200, 300] # R hip
    xy[13] = [200, 350] # R knee
    
    return {"xy": xy, "conf": conf}

kp = mock_pose()
side, diff = _detect_closer_side(kp["xy"], kp["conf"], 0.0)
print(f"Side detected: {side}, Diff: {diff}")
if side:
    feats = squat_features_for_frame(kp["xy"], kp["conf"], side)
    print(f"Feats: {feats}")
else:
    print("No side detected!")
