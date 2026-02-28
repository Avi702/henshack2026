import os
import numpy as np
from scipy.interpolate import interp1d

# ==========================================
# 1. CONFIGURATION & INDICES
# ==========================================
# MediaPipe Landmark Indices (from your reference)
MP_IDX = {
    "l_shoulder": 11, "r_shoulder": 12,
    "l_hip": 23,      "r_hip": 24,
    "l_knee": 25,     "r_knee": 26,
    "l_ankle": 27,    "r_ankle": 28
}

TARGET_FRAMES = 100

# ==========================================
# 2. MATH FUNCTIONS
# ==========================================
def angle_abc(a, b, c):
    """Calculates the 2D angle at point b formed by a-b-c, in degrees."""
    # Convert lists to numpy arrays
    a, b, c = np.array(a), np.array(b), np.array(c)
    
    ba = a - b
    bc = c - b
    denom = (np.linalg.norm(ba) * np.linalg.norm(bc))
    if denom < 1e-6:
        return np.nan
    cosang = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosang)))

def get_joint(row, joint_name):
    """Extracts [x, y, z, visibility] for a specific joint from the 132-value row."""
    idx = MP_IDX[joint_name]
    start = idx * 4
    # We return [x, y], z, visibility
    return [row[start], row[start+1]], row[start+2], row[start+3]

# ==========================================
# 3. INTERPOLATION FUNCTION (The "Stretcher")
# ==========================================
def interpolate_tensor(angles_array, target_length=100):
    """Stretches or shrinks an array of shape (N, 3) to (100, 3) and removes NaNs."""
    N = angles_array.shape[0]
    
    # Create the old timeline (e.g., 0.0 to 1.0 spread across N frames)
    old_time = np.linspace(0, 1, N)
    # Create the new timeline (0.0 to 1.0 spread across 100 frames)
    new_time = np.linspace(0, 1, target_length)
    
    resampled_array = np.zeros((target_length, 3))
    
    for col_idx in range(3):
        col_data = angles_array[:, col_idx]
        
        # 1. Clean NaNs (Find valid numbers and ignore NaNs)
        valid_mask = ~np.isnan(col_data)
        
        if valid_mask.sum() == 0:
            # If the entire column is broken, fill with zeros
            resampled_array[:, col_idx] = 0.0
            continue
            
        valid_time = old_time[valid_mask]
        valid_data = col_data[valid_mask]
        
        # 2. Interpolate
        # We use a linear equation to map the old valid points to the new 100 points
        interpolator = interp1d(valid_time, valid_data, kind='linear', fill_value="extrapolate")
        resampled_array[:, col_idx] = interpolator(new_time)
        
    return resampled_array

# ==========================================
# 4. MAIN PROCESSING LOOP
# ==========================================
def convert_mediapipe_file(input_path, output_path):
    # Load the (N, 132) array
    data_mp = np.load(input_path)
    num_frames = data_mp.shape[0]
    
    angles_per_frame = []
    
    for i in range(num_frames):
        row = data_mp[i]
        
        # Extract z-depth to determine which side is facing the camera
        _, l_hip_z, _ = get_joint(row, "l_hip")
        _, r_hip_z, _ = get_joint(row, "r_hip")
        
        # Smaller (more negative) Z means closer to camera in MediaPipe
        closest_side = "left" if l_hip_z < r_hip_z else "right"
        
        # Setup prefixes
        side = "l_" if closest_side == "left" else "r_"
        other = "r_" if closest_side == "left" else "l_"
        
        # Extract 2D [x, y] coordinates
        shoulder, _, _  = get_joint(row, side + "shoulder")
        hip, _, _       = get_joint(row, side + "hip")
        knee, _, _      = get_joint(row, side + "knee")
        ankle, _, _     = get_joint(row, side + "ankle")
        other_hip, _, _ = get_joint(row, other + "hip")
        
        # Compute the 3 Angles (Same as YOLO logic)
        ang1 = angle_abc(shoulder, hip, knee)    # Shoulder-Hip-Knee
        ang2 = angle_abc(other_hip, hip, knee)   # OtherHip-Hip-Knee
        ang3 = angle_abc(hip, knee, ankle)       # Hip-Knee-Ankle
        
        angles_per_frame.append([ang1, ang2, ang3])
        
    # Convert list to array: Shape becomes (N, 3)
    angles_np = np.asarray(angles_per_frame, dtype=np.float32)
    
    # Interpolate to exactly 100 frames: Shape becomes (100, 3)
    final_tensor = interpolate_tensor(angles_np, target_length=TARGET_FRAMES)
    
    # Save the finalized, ready-to-train file
    np.save(output_path, final_tensor)
    print(f"Processed: {os.path.basename(input_path)} | Final Shape: {final_tensor.shape}")

# ==========================================
# 5. BATCH PROCESSING FOLDER
# ==========================================
if __name__ == "__main__":
    INPUT_DIR = "raw_mediapipe_numpy"
    OUTPUT_DIR = "training_tensors/squats/"
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Loop through all files in the directory
    if os.path.exists(INPUT_DIR):
        for file_name in os.listdir(INPUT_DIR):
            if file_name.endswith(".npy"):
                in_path = os.path.join(INPUT_DIR, file_name)
                out_path = os.path.join(OUTPUT_DIR, file_name)
                
                convert_mediapipe_file(in_path, out_path)
    else:
        print(f"Please create the directory '{INPUT_DIR}' and put your (N, 132) .npy files there.")