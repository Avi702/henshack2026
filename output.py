import os
import argparse
import numpy as np
import torch
import torch.nn as nn

# ==========================================
# 1. THE UNIVERSAL AUTOENCODER MODEL
# (Must match the training architecture exactly)
# ==========================================
class PoseAutoencoder(nn.Module):
    # Notice we must match the neuralnet.py dimensions (128 and 32)
    def __init__(self, num_features, hidden_dim=128, latent_dim=32):
        super(PoseAutoencoder, self).__init__()
        
        # Dropout added to match training script
        self.encoder_lstm = nn.LSTM(
            input_size=num_features, 
            hidden_size=hidden_dim, 
            num_layers=2, 
            batch_first=True,
            dropout=0.2 
        )
        self.encoder_linear = nn.Linear(hidden_dim, latent_dim)
        
        # Non-linear activation added to match training script
        self.activation = nn.ReLU()
        
        self.decoder_linear = nn.Linear(latent_dim, hidden_dim)
        self.decoder_lstm = nn.LSTM(
            input_size=hidden_dim, 
            hidden_size=hidden_dim, 
            num_layers=2, 
            batch_first=True,
            dropout=0.2
        )
        self.output_layer = nn.Linear(hidden_dim, num_features)

    def forward(self, x):
        _, (hidden, _) = self.encoder_lstm(x)
        last_hidden = hidden[-1]
        
        latent_raw = self.encoder_linear(last_hidden)
        latent = self.activation(latent_raw)
        
        decoded_raw = self.decoder_linear(latent)
        decoded_hidden = self.activation(decoded_raw)
        
        repeated_hidden = decoded_hidden.unsqueeze(1).repeat(1, x.size(1), 1)
        decoder_out, _ = self.decoder_lstm(repeated_hidden)
        
        return self.output_layer(decoder_out)

# ==========================================
# 2. FEEDBACK THRESHOLDS & CONFIGURATION
# ==========================================
# These thresholds represent the maximum allowed error (in degrees) 
# before the AI flags it as bad form. You can tweak these later!
LIFT_CONFIGS = {
    'squat': {
        'model_path': 'squat_expert.pt',
        'features': 3,
        'thresholds': [12.0, 10.0, 15.0], 
        'feedback': [
            "Torso/Hip Anomaly: Your back angle deviated heavily from a perfect lift. Make sure your hips aren't shooting up too fast (avoid the 'good morning' squat).",
            "Stance/Shift Anomaly: Your hip/knee tracking looks asymmetrical. Ensure you are pushing evenly off both legs and your knees are tracking over your toes.",
            "Knee Angle Anomaly: Your depth and knee flexion didn't match professional mechanics. You likely cut the squat high—try to sink your hips below parallel."
        ]
    },
    'bench': {
        'model_path': 'bench_expert.pt',
        'features': 3,
        'thresholds': [10.0, 10.0, 8.0],
        'feedback': [
            "Elbow Flare Anomaly: Your elbow angle deviated from the ideal path. Try to keep your elbows tucked at a 45-degree angle to protect your shoulders.",
            "Shoulder/Arch Anomaly: You may have lost tightness in your upper back. Pinch your shoulder blades together and keep your chest up.",
            "Bar Path Anomaly: The bar didn't follow the optimal J-curve. Make sure you are touching lower on your chest and pressing back toward your face."
        ]
    },
    'deadlift': {
        'model_path': 'deadlift_expert.pt',
        'features': 3,
        'thresholds': [12.0, 15.0, 10.0],
        'feedback': [
            "Back Rounding Anomaly: Severe deviation in your spinal alignment. Drop the weight, brace your core tighter, and keep your lats engaged.",
            "Hip Hinge Anomaly: Your hips were either too high or too low at the start. Build tension in your hamstrings before pulling.",
            "Bar Path Anomaly: The bar drifted away from your body. Keep the barbell dragging tightly against your shins and quads the whole time."
        ]
    }
}

# ==========================================
# 3. THE INFERENCE ENGINE
# ==========================================
def generate_feedback(npy_file_path, lift_type):
    config = LIFT_CONFIGS.get(lift_type)
    if not config:
        print(f"Error: Unknown lift type '{lift_type}'.")
        return

    # 1. Load the User's Data
    if not os.path.exists(npy_file_path):
        print(f"Error: File '{npy_file_path}' not found.")
        return
        
    user_data = np.load(npy_file_path) # Shape should be (100, 3)
    user_tensor = torch.tensor(user_data, dtype=torch.float32).unsqueeze(0)

    # 2. Load the Trained Model
    model_path = config['model_path']
    if not os.path.exists(model_path):
        print(f"Error: Trained model '{model_path}' not found. Did you run the training script yet?")
        return

    model = PoseAutoencoder(num_features=config['features'])
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    model.eval() 

    # 3. Calculate Reconstruction Error
    with torch.no_grad():
        reconstruction = model(user_tensor)
    
    # Subtract reconstruction from original and get absolute error (Shape: 100, 3)
    error_matrix = torch.abs(user_tensor - reconstruction).squeeze().numpy()

    # --- NEW: SAVE THE ERROR ARRAY ---
    # Creates a file like "user_squat_attempt_error.npy" in the same folder
    base_name = os.path.splitext(os.path.basename(npy_file_path))[0]
    error_file_path = f"{base_name}_error.npy"
    np.save(error_file_path, error_matrix)
    print(f"\n💾 Saved raw error data to: {error_file_path}")
    # ---------------------------------

    # 4. Generate Feedback
    print(f"\n{'='*50}")
    print(f" AI LIFT ANALYSIS: {lift_type.upper()}")
    print(f"{'='*50}")
    
    issues_found = False
    
    # Loop through each of the 3 features (angles)
# Loop through each of the 3 features (angles)
    for col_idx in range(config['features']):
        # OLD: max_error = np.max(error_matrix[:, col_idx])
        
        # NEW: Use 95th Percentile to ignore 1-frame camera glitches!
        max_error = np.percentile(error_matrix[:, col_idx], 95)
        
        threshold = config['thresholds'][col_idx]
        
        if max_error > threshold:
            issues_found = True
            print(f"❌ TRIGGERED: {config['feedback'][col_idx]}")
            print(f"   (Max Error: {max_error:.1f}° | Threshold: {threshold:.1f}°)\n")
            
    if not issues_found:
        print("✅ PERFECT FORM: No anomalies detected. Your lift mathematically matched professional biomechanics!")
        print("   Keep up the great work.\n")

# ==========================================
# 4. COMMAND LINE INTERFACE
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a lift using trained Autoencoder")
    parser.add_argument('--lift', type=str, required=True, choices=['squat', 'bench', 'deadlift'],
                        help="Which lift are you analyzing?")
    parser.add_argument('--file', type=str, required=True,
                        help="Path to the user's interpolated 100-frame .npy file")
                        
    args = parser.parse_args()
    
    generate_feedback(args.file, args.lift)