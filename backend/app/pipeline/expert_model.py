"""Load a trained PoseAutoencoder and compute reconstruction error.

The ``PoseAutoencoder`` architecture is duplicated here (mirroring
``neuralnet.py``) so that the backend can load weights without importing
from the project root.  The original ``neuralnet.py`` is **not** modified.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

log = logging.getLogger(__name__)

# ── Lift configs (mirrors neuralnet.py LIFT_CONFIGS) ───────
LIFT_CONFIGS = {
    "squat": {"num_features": 3, "save_name": "squat_expert.pt"},
    "bench": {"num_features": 3, "save_name": "bench_expert.pt"},
    "deadlift": {"num_features": 3, "save_name": "deadlift_expert.pt"},
}

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ── Architecture (exact copy from neuralnet.py PoseAutoencoder) ─────
class PoseAutoencoder(nn.Module):
    def __init__(self, num_features: int, hidden_dim: int = 128, latent_dim: int = 32):
        super().__init__()
        self.encoder_lstm = nn.LSTM(
            input_size=num_features,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=0.2,
        )
        self.encoder_linear = nn.Linear(hidden_dim, latent_dim)
        self.activation = nn.ReLU()

        self.decoder_linear = nn.Linear(latent_dim, hidden_dim)
        self.decoder_lstm = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=0.2,
        )
        self.output_layer = nn.Linear(hidden_dim, num_features)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        _, (hidden, _) = self.encoder_lstm(x)
        last_hidden = hidden[-1]

        latent_raw = self.encoder_linear(last_hidden)
        latent = self.activation(latent_raw)

        decoded_raw = self.decoder_linear(latent)
        decoded_hidden = self.activation(decoded_raw)

        repeated = decoded_hidden.unsqueeze(1).repeat(1, x.size(1), 1)
        decoder_out, _ = self.decoder_lstm(repeated)
        return self.output_layer(decoder_out)


# ── Loading + inference ────────────────────────────────────

def load_expert(lift_type: str, models_dir: str | Path | None = None) -> PoseAutoencoder | None:
    """Load a saved ``{lift}_expert.pt`` model.

    Search order:
      1. *models_dir*  (``backend/models/``)
      2. project root  (where neuralnet.py lives)

    Returns ``None`` if no checkpoint is found.
    """
    cfg = LIFT_CONFIGS[lift_type]
    filename = cfg["save_name"]
    search_dirs: list[Path] = []
    if models_dir:
        search_dirs.append(Path(models_dir))
    search_dirs.append(_PROJECT_ROOT)

    ckpt_path: Path | None = None
    for d in search_dirs:
        candidate = d / filename
        if candidate.exists():
            ckpt_path = candidate
            break

    if ckpt_path is None:
        log.warning("No checkpoint found for '%s' (searched %s)", lift_type, search_dirs)
        return None

    log.info("Loading expert model from %s", ckpt_path)
    model = PoseAutoencoder(num_features=cfg["num_features"])
    model.load_state_dict(torch.load(ckpt_path, map_location="cpu", weights_only=True))
    model.eval()
    return model


def compute_mse(
    model: PoseAutoencoder,
    features: np.ndarray,
) -> tuple[float, np.ndarray, np.ndarray]:
    """Run *features* through the autoencoder.

    Parameters
    ----------
    model : PoseAutoencoder
    features : np.ndarray, shape (T, F)

    Returns
    -------
    mean_mse : float
    per_frame_mse : np.ndarray, shape (T,)
    reconstruction : np.ndarray, shape (T, F)
    """
    # Normalize to [0, 1] to match training (neuralnet.py divides by 180)
    x_norm = torch.tensor(features / 180.0, dtype=torch.float32).unsqueeze(0)  # (1, T, F)
    with torch.no_grad():
        x_hat_norm = model(x_norm)
    per_frame = ((x_norm - x_hat_norm) ** 2).mean(dim=2).squeeze(0).numpy()  # (T,)
    # Denormalize reconstruction back to degrees for downstream use
    recon = x_hat_norm.squeeze(0).numpy() * 180.0  # (T, F)
    log.info("compute_mse: mean=%.5f, max=%.5f over %d frames", per_frame.mean(), per_frame.max(), len(per_frame))
    return float(per_frame.mean()), per_frame, recon
