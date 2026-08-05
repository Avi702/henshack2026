# SquatBuddy

A computer vision and machine learning system that analyzes squat form from video and provides localized, frame-level feedback.

SquatBuddy was built to evaluate lifting technique without requiring a large labeled dataset of incorrect form. Instead, it learns the movement patterns of expert lifters and flags deviations using reconstruction error from an LSTM autoencoder.

[View on Devpost](https://devpost.com/software/squatbuddy)

## Highlights

- Trained a **2-layer LSTM autoencoder** on joint-angle sequences from **120+ expert squat videos**
- Framed form assessment as **unsupervised anomaly detection**, avoiding the need for labeled bad-form examples
- Designed a phase-anchoring algorithm that normalizes variable-length repetitions into a fixed-length sequence
- Mapped model error back onto original video frames for frame-accurate visual feedback
- Decomposed reconstruction error by biomechanical feature to identify specific issues instead of returning one opaque score
- Built an end-to-end application with a FastAPI backend, Next.js frontend, and OpenCV video rendering

> SquatBuddy currently focuses on squat analysis. Bench press and deadlift support are not included in the current trained system.

## Architecture

```text
┌──────────────────────────┐
│      Next.js Frontend    │
│                          │
│  Video Upload            │
│  Analysis Request        │
│  Results and Feedback    │
│  Annotated Video Output  │
└─────────────┬────────────┘
              │
              │ REST API
              ▼
┌──────────────────────────┐
│       FastAPI Backend    │
│                          │
│  Video Validation        │
│  Pose Estimation         │
│  Feature Extraction      │
│  Model Inference         │
│  Feedback Generation     │
│  Video Rendering         │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│   ML Analysis Pipeline   │
│                          │
│  Pose Keypoints          │
│  Joint-Angle Sequences   │
│  Phase Normalization     │
│  LSTM Autoencoder        │
│  Reconstruction Error    │
│  Localized Feedback      │
└──────────────────────────┘
```

## How It Works

```text
Upload Squat Video
        ↓
Decode Video Frames
        ↓
Estimate Body Pose
        ↓
Extract Biomechanical Features
        ↓
Detect Bottom of the Repetition
        ↓
Normalize Descent and Ascent Phases
        ↓
Run LSTM Autoencoder Inference
        ↓
Compute Per-Frame and Per-Feature Error
        ↓
Map Errors Back to Original Frames
        ↓
Generate Feedback and Annotated Video
```

## Machine Learning Approach

Most exercise-form classifiers require examples labeled as correct or incorrect. High-quality labeled examples of bad lifting form are difficult to collect and can vary significantly between lifters.

SquatBuddy instead uses an LSTM autoencoder trained only on expert squat sequences.

During inference:

1. The model receives a normalized sequence of biomechanical features
2. It attempts to reconstruct the expert-like movement pattern
3. Reconstruction error is calculated for every frame and feature
4. Larger errors indicate movement that differs from the learned expert distribution

This allows the system to identify unusual movement patterns without training a separate class for every possible form issue.

## Feature Extraction

Pose keypoints are converted into biomechanical features such as:

- Hip angle
- Knee angle
- Torso position
- Lateral hip movement
- Relative joint alignment

The pipeline selects the more visible side of the body using estimated limb lengths. An exponential moving average and dead zone reduce rapid switching between left and right sides when pose estimates are noisy.

## Phase Anchoring

Squat repetitions vary in speed and duration, so raw frame sequences cannot be compared directly.

SquatBuddy normalizes each repetition by:

1. Detecting the bottom of the squat using the minimum hip angle
2. Splitting the repetition into descent and ascent
3. Resampling each phase to 50 frames
4. Combining both phases into a fixed 100-frame sequence

```text
Variable-Length Squat
        ↓
Detect Bottom Position
        ↓
Descent → 50 Frames
Ascent  → 50 Frames
        ↓
Fixed 100-Frame Sequence
```

The pipeline also stores the inverse transformation so model errors can be projected back onto the original video timeline.

## Interpretable Feedback

SquatBuddy preserves reconstruction error as a two-dimensional matrix:

```text
Time × Biomechanical Feature
```

Instead of returning only a single score, the system can identify:

- Which feature deviated most
- When the deviation occurred
- The severity of the issue
- The video frame that best demonstrates the problem

This supports feedback for issues such as excessive torso lean, lateral hip shift, and knee-tracking deviations.

## Annotated Video Output

The backend renders an output video containing:

- Pose skeleton overlays
- Highlighted frames with elevated reconstruction error
- Per-feature comparison between observed and reconstructed movement
- Localized feedback tied to specific portions of the repetition

The inverse phase mapping keeps model output aligned with the original frames.

## Repository Structure

```text
squatbuddy/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI routes
│   │   ├── schemas.py               # Request and response models
│   │   └── pipeline/
│   │       ├── video_io.py          # Video decoding and validation
│   │       ├── pose.py              # Pose estimation
│   │       ├── features.py          # Feature extraction and phase anchoring
│   │       ├── expert_model.py      # LSTM autoencoder inference
│   │       ├── feedback.py          # Error analysis and feedback
│   │       ├── overlay.py           # Visual overlays
│   │       └── render.py            # Annotated video rendering
│   ├── requirements.txt
│   └── models/                      # Trained model weights
│
├── frontend/
│   ├── app/                         # Next.js pages
│   ├── components/                  # Upload and result components
│   └── lib/                         # API utilities
│
├── training/
│   ├── neuralnet.py                 # LSTM autoencoder definition
│   ├── training data processing
│   └── model training scripts
│
└── README.md
```

## Technology Stack

### Machine Learning and Computer Vision

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white)

### Backend

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=flat-square&logo=pydantic&logoColor=white)

### Frontend

![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)

## Local Development

### Requirements

- Python 3.10+
- Node.js
- npm
- FFmpeg

### Clone the Repository

```bash
git clone https://github.com/mustafa-afzal/squatbuddy.git
cd squatbuddy
```

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn app.main:app --reload
```

The backend will run at:

```text
http://localhost:8000
```

### Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will run at:

```text
http://localhost:3000
```

## Engineering Challenges

Some of the main challenges addressed in SquatBuddy include:

- Evaluating form without a large labeled incorrect-form dataset
- Converting noisy pose keypoints into stable biomechanical features
- Comparing repetitions performed at different speeds
- Mapping normalized model output back to original video frames
- Translating model loss into understandable user feedback
- Rendering pose, error, and feature information into a final video
- Serving a compute-heavy video pipeline through a web application

## Evaluation

The current model uses reconstruction error to identify deviations from expert movement patterns.

A stronger future evaluation would include:

- A held-out set of expert squat videos
- Labeled incorrect-form examples
- ROC and precision-recall analysis
- Threshold selection based on validation data
- Per-fault evaluation for different movement issues

No formal accuracy or AUC claim is included until this evaluation is completed.

## Known Limitations

- The trained system currently supports squats only
- Analysis quality depends on camera angle, visibility, lighting, and pose-estimation accuracy
- The model may flag harmless differences in body proportions or lifting style
- Reconstruction error indicates deviation from the training distribution, not a medical diagnosis
- The current classification threshold requires more formal validation
- Long-running video analysis is handled within the request rather than through a dedicated job queue
- Automated test coverage and deployment infrastructure are limited

## Future Improvements

- Evaluate the model on held-out correct and incorrect-form datasets
- Select anomaly thresholds using ROC analysis
- Add support for additional lifts after collecting sufficient training data
- Move video processing to background jobs with progress tracking
- Add unit tests for feature extraction, phase anchoring, and inverse mapping
- Add Docker and CI support
- Improve handling of multiple repetitions in one video
- Measure inference time and optimize video-processing latency

## Disclaimer

SquatBuddy is an educational fitness-analysis project. Its feedback is not medical advice and should not replace guidance from a qualified coach, physical therapist, or healthcare professional.

## License

MIT
