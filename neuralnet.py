import os
import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau # NEW: Scheduler
from torch.utils.data import Dataset, DataLoader

# ==========================================
# 1. THE DATASET LOADER (UPGRADED)
# ==========================================
class LiftDataset(Dataset):
    def __init__(self, data_dir, add_noise=True):
        self.data_dir = data_dir
        self.add_noise = add_noise
        self.files = [f for f in os.listdir(data_dir) if f.endswith('.npy')]
        
        if len(self.files) == 0:
            print(f"⚠️ Warning: No .npy files found in {data_dir}")
            
    def __len__(self):
        return len(self.files)
        
    def __getitem__(self, idx):
        file_path = os.path.join(self.data_dir, self.files[idx])
        data = np.load(file_path).astype(np.float32)
        
        # --- NEW: NORMALIZATION ---
        # Scale 0-180 degrees down to 0.0 - 1.0 range
        data = data / 180.0 
        
        # --- NEW: DATA AUGMENTATION ---
        # Inject microscopic noise to artificially expand the 120 video dataset
        if self.add_noise:
            # 0.01 in normalized space is about 1.8 degrees of variance
            noise = np.random.normal(0, 0.01, data.shape).astype(np.float32)
            data = data + noise
            
        return torch.tensor(data)

# ==========================================
# 2. THE UNIVERSAL AUTOENCODER MODEL
# ==========================================
class PoseAutoencoder(nn.Module):
    def __init__(self, num_features, hidden_dim=128, latent_dim=32):
        super(PoseAutoencoder, self).__init__()
        
        self.encoder_lstm = nn.LSTM(
            input_size=num_features, 
            hidden_size=hidden_dim, 
            num_layers=2, 
            batch_first=True,
            dropout=0.2 
        )
        self.encoder_linear = nn.Linear(hidden_dim, latent_dim)
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
        
        reconstruction = self.output_layer(decoder_out)
        return reconstruction

# ==========================================
# 3. MASTER CONFIGURATION & TRAINING LOGIC
# ==========================================
LIFT_CONFIGS = {
    'squat': {
        'data_dir': 'training_tensors/squats_phase100/',
        'num_features': 3,
        'save_name': 'squat_expert.pt'
    },
    'bench': {
        'data_dir': 'training_tensors/bench/',
        'num_features': 3, 
        'save_name': 'bench_expert.pt'
    },
    'deadlift': {
        'data_dir': 'training_tensors/deadlifts/',
        'num_features': 3, 
        'save_name': 'deadlift_expert.pt'
    }
}

def train_autoencoder(lift_type, epochs, batch_size, learning_rate):
    config = LIFT_CONFIGS[lift_type]
    
    print(f"\n{'='*40}")
    print(f" TRAINING EXPERT MODEL: {lift_type.upper()}")
    print(f"{'='*40}")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    dataset = LiftDataset(data_dir=config['data_dir'], add_noise=True)
    if len(dataset) == 0:
        return 
        
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    model = PoseAutoencoder(num_features=config['num_features']).to(device)
    
    if os.path.exists(config['save_name']):
        print(f"🔄 Found existing model '{config['save_name']}'. Loading weights...")
        model.load_state_dict(torch.load(config['save_name'], map_location=device))
    else:
        print("🚀 Starting training from scratch...")

    criterion = nn.MSELoss() 
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # --- NEW: SCHEDULER ---
    # If loss doesn't drop for 10 epochs, cut learning rate by 50%
    scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=10)
    
    best_loss = float('inf')

    model.train()
    for epoch in range(epochs):
        total_loss = 0.0
        for batch_data in dataloader:
            batch_data = batch_data.to(device)
            
            reconstruction = model(batch_data)
            loss = criterion(reconstruction, batch_data)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        avg_loss = total_loss / len(dataloader)
        
        # Step the scheduler based on the current epoch's loss
        scheduler.step(avg_loss)
        
        saved_flag = ""
        if avg_loss < best_loss:
            best_loss = avg_loss
            torch.save(model.state_dict(), config['save_name'])
            saved_flag = "💾 [NEW BEST SAVED]"
        
        if (epoch + 1) % 10 == 0 or epoch == 0 or saved_flag:
            print(f"Epoch [{epoch+1}/{epochs}] | MSE Loss: {avg_loss:.6f} {saved_flag}")

    print(f"\n✅ Training Complete! Best MSE Loss: {best_loss:.6f}")

if __name__ == "__main__":
    for lift, cfg in LIFT_CONFIGS.items():
        os.makedirs(cfg['data_dir'], exist_ok=True)
        
    parser = argparse.ArgumentParser(description="Train a Biomechanics Expert Autoencoder")
    parser.add_argument('--lift', type=str, required=True, choices=['squat', 'bench', 'deadlift'])
    parser.add_argument('--epochs', type=int, default=150)
    parser.add_argument('--batch', type=int, default=16)
    parser.add_argument('--lr', type=float, default=0.001)
                        
    args = parser.parse_args()
    
    train_autoencoder(args.lift, args.epochs, args.batch, args.lr)