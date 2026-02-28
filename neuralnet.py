import os
import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# ==========================================
# 1. THE DATASET LOADER
# ==========================================
class LiftDataset(Dataset):
    def __init__(self, data_dir):
        """Loads all .npy files from the specified directory."""
        self.data_dir = data_dir
        self.file_names = [f for f in os.listdir(data_dir) if f.endswith('.npy')]
        
        if len(self.file_names) == 0:
            print(f"Warning: No .npy files found in {data_dir}. Add data before training!")

    def __len__(self):
        return len(self.file_names)

    def __getitem__(self, idx):
        file_path = os.path.join(self.data_dir, self.file_names[idx])
        data = np.load(file_path)
        return torch.tensor(data, dtype=torch.float32)

# ==========================================
# 2. THE UNIVERSAL AUTOENCODER MODEL
# ==========================================
class PoseAutoencoder(nn.Module):
    def __init__(self, num_features, hidden_dim=64, latent_dim=16):
        super(PoseAutoencoder, self).__init__()
        
        # ENCODER: Compresses the time-series
        self.encoder_lstm = nn.LSTM(
            input_size=num_features, 
            hidden_size=hidden_dim, 
            num_layers=2, 
            batch_first=True
        )
        self.encoder_linear = nn.Linear(hidden_dim, latent_dim)
        
        # DECODER: Reconstructs the time-series
        self.decoder_linear = nn.Linear(latent_dim, hidden_dim)
        self.decoder_lstm = nn.LSTM(
            input_size=hidden_dim, 
            hidden_size=hidden_dim, 
            num_layers=2, 
            batch_first=True
        )
        self.output_layer = nn.Linear(hidden_dim, num_features)

    def forward(self, x):
        # Encode
        _, (hidden, _) = self.encoder_lstm(x)
        last_hidden = hidden[-1]
        latent = self.encoder_linear(last_hidden)
        
        # Decode
        decoded_hidden = self.decoder_linear(latent)
        # Repeat the hidden state for every frame in the sequence
        repeated_hidden = decoded_hidden.unsqueeze(1).repeat(1, x.size(1), 1)
        decoder_out, _ = self.decoder_lstm(repeated_hidden)
        
        # Final output mapping back to features
        reconstruction = self.output_layer(decoder_out)
        return reconstruction

# ==========================================
# 3. MASTER CONFIGURATION & TRAINING LOGIC
# ==========================================
LIFT_CONFIGS = {
    'squat': {
        'data_dir': './training_tensors/squats/',
        'num_features': 4, # Knee, Hip, Spine, Bar Path X
        'save_name': 'squat_expert.pt'
    },
    'bench': {
        'data_dir': './training_tensors/bench/',
        'num_features': 3, # Elbow, Shoulder, Bar Path Diagonal
        'save_name': 'bench_expert.pt'
    },
    'deadlift': {
        'data_dir': './training_tensors/deadlifts/',
        'num_features': 3, # Back Rounding, Hip Hinge, Bar-to-Shin Distance
        'save_name': 'deadlift_expert.pt'
    }
}

def train_autoencoder(lift_type, epochs, batch_size, learning_rate):
    config = LIFT_CONFIGS[lift_type]
    
    print(f"\n{'='*40}")
    print(f" TRAINING EXPERT MODEL: {lift_type.upper()}")
    print(f"{'='*40}")
    print(f"Data Directory : {config['data_dir']}")
    print(f"Input Features : {config['num_features']} per frame")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Compute Device : {device}\n")
    
    # Initialize DataLoader
    dataset = LiftDataset(data_dir=config['data_dir'])
    if len(dataset) == 0:
        return # Abort if no data
        
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Initialize Model, Loss, and Optimizer
    model = PoseAutoencoder(num_features=config['num_features']).to(device)
    criterion = nn.MSELoss() 
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Training Loop
    model.train()
    for epoch in range(epochs):
        total_loss = 0.0
        for batch_data in dataloader:
            batch_data = batch_data.to(device)
            
            # Forward pass & Reconstruction
            reconstruction = model(batch_data)
            loss = criterion(reconstruction, batch_data)
            
            # Backpropagation
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        # Logging
        if (epoch + 1) % 20 == 0 or epoch == 0:
            avg_loss = total_loss / len(dataloader)
            print(f"Epoch [{epoch+1}/{epochs}] | MSE Loss: {avg_loss:.5f}")

    # Save the finalized expert model
    torch.save(model.state_dict(), config['save_name'])
    print(f"\nSuccess! Expert saved as '{config['save_name']}'")

# ==========================================
# 4. COMMAND LINE INTERFACE (CLI)
# ==========================================
if __name__ == "__main__":
    # Ensure directories exist
    for lift, cfg in LIFT_CONFIGS.items():
        os.makedirs(cfg['data_dir'], exist_ok=True)
        
    # Setup Argument Parser
    parser = argparse.ArgumentParser(description="Train a Biomechanics Expert Autoencoder")
    
    parser.add_argument('--lift', type=str, required=True, choices=['squat', 'bench', 'deadlift'],
                        help="Which lift model do you want to train?")
    parser.add_argument('--epochs', type=int, default=100, 
                        help="Number of training loops (default: 100)")
    parser.add_argument('--batch', type=int, default=16, 
                        help="Batch size for training (default: 16)")
    parser.add_argument('--lr', type=float, default=0.001, 
                        help="Learning rate (default: 0.001)")
                        
    args = parser.parse_args()
    
    # Execute training with CLI arguments
    train_autoencoder(
        lift_type=args.lift, 
        epochs=args.epochs, 
        batch_size=args.batch, 
        learning_rate=args.lr
    )