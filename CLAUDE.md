# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a biomechanics analysis system for evaluating weightlifting form (squats, bench press, deadlifts) using computer vision and deep learning. The system uses YOLOv8 pose estimation to track body movements in real-time, then applies autoencoder neural networks to assess exercise technique against "expert" form patterns.

## Architecture

### Two-Phase System

1. **Real-time Pose Tracking** (`body_tracking.py`):
   - Uses YOLOv8n-pose model (`yolov8n-pose.pt`) for 17-keypoint COCO pose detection
   - Captures webcam input and overlays skeleton visualization
   - COCO keypoints follow specific indexing (see `COCO_KPTS` list in body_tracking.py:15-20)
   - Note: Frame is horizontally flipped for mirror effect (line 43)

2. **Neural Network Training** (`neuralnet.py`):
   - LSTM-based autoencoder that learns "expert" movement patterns per lift type
   - Separate models for squat, bench press, and deadlift
   - Each lift type has different feature counts:
     - Squat: 4 features (Knee, Hip, Spine, Bar Path X)
     - Bench: 3 features (Elbow, Shoulder, Bar Path Diagonal)
     - Deadlift: 3 features (Back Rounding, Hip Hinge, Bar-to-Shin Distance)
   - Trained models saved as `{lift}_expert.pt` files

### Data Pipeline

- **Training Data**: Stored as `.npy` files in `./training_tensors/{lift_type}/`
  - Squat data: `./training_tensors/squats/`
  - Bench data: `./training_tensors/bench/`
  - Deadlift data: `./training_tensors/deadlifts/`
- **Validation Data**: `Valid/` directory contains 120+ subdirectories (0-119), each with multiple `.npy` files containing pose keypoint sequences (shape: 132,)

## Key Commands

### Running Pose Tracking
```bash
python body_tracking.py
```
- Opens webcam feed with real-time pose estimation
- Press 'q' to quit
- Requires camera access

### Training Autoencoder Models
```bash
# Train squat expert model
python neuralnet.py --lift squat --epochs 100 --batch 16 --lr 0.001

# Train bench press expert model
python neuralnet.py --lift bench --epochs 100 --batch 16 --lr 0.001

# Train deadlift expert model
python neuralnet.py --lift deadlift --epochs 100 --batch 16 --lr 0.001
```

Parameters:
- `--lift`: Required. Choose from 'squat', 'bench', or 'deadlift'
- `--epochs`: Training iterations (default: 100)
- `--batch`: Batch size (default: 16)
- `--lr`: Learning rate (default: 0.001)

## Dependencies

Core libraries (install via pip):
- `torch` - PyTorch for neural network training
- `ultralytics` - YOLOv8 pose estimation
- `opencv-python` (cv2) - Video capture and display
- `numpy` - Numerical operations

## Important Implementation Details

### Keypoint Indexing
The COCO 17-keypoint format has specific index mappings (body_tracking.py:14-20). When working with pose data, always reference the `COCO_KPTS` list rather than hardcoding indices.

### Mirrored Coordinates
The webcam frame is horizontally flipped (body_tracking.py:43), so left/right keypoint interpretations are inverted from the model's perspective. Keep this in mind when debugging coordinate-based features.

### Model Architecture
The `PoseAutoencoder` (neuralnet.py:32-69) uses:
- 2-layer bidirectional LSTM encoder
- Linear compression to latent space (16 dimensions)
- 2-layer LSTM decoder with repeated hidden states
- MSE loss for reconstruction

### Configuration System
Lift-specific configurations are centralized in the `LIFT_CONFIGS` dictionary (neuralnet.py:74-90). When adding new lift types or modifying features, update this dictionary rather than changing logic throughout the code.
