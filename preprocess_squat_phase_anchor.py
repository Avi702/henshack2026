"""Phase-anchored interpolation for squat training data.

Re-samples each squat .npy so the hole (lowest knee angle) lands
at the exact midpoint of the output sequence. This prevents the
autoencoder from overfitting to absolute time position.
"""

import argparse
import os
import sys

import numpy as np
from scipy.interpolate import interp1d


# ── Core preprocessing function ─────────────────────────────
def phase_anchored_interpolation(raw_angles, total_frames=100):
    num_raw_frames = raw_angles.shape[0]
    hole_idx = np.argmin(raw_angles[:, 0])
    if hole_idx < 5 or hole_idx > num_raw_frames - 5:
        print("⚠️ Warning: Could not clearly detect the squat hole. Falling back to standard split.")
        hole_idx = num_raw_frames // 2

    descent_data = raw_angles[:hole_idx + 1, :]
    ascent_data = raw_angles[hole_idx:, :]

    half_frames = total_frames // 2
    time_descent = np.linspace(0, 1, len(descent_data))
    time_ascent = np.linspace(0, 1, len(ascent_data))
    target_time = np.linspace(0, 1, half_frames)

    interp_descent = interp1d(time_descent, descent_data, axis=0, kind='linear')
    normalized_descent = interp_descent(target_time)

    interp_ascent = interp1d(time_ascent, ascent_data, axis=0, kind='linear')
    normalized_ascent = interp_ascent(target_time)

    final_normalized_lift = np.vstack((normalized_descent, normalized_ascent))
    return final_normalized_lift.astype(np.float32)


# ── Batch processing ────────────────────────────────────────
def process_directory(in_dir, out_dir, total_frames, overwrite):
    os.makedirs(out_dir, exist_ok=True)

    npy_files = sorted([f for f in os.listdir(in_dir) if f.endswith(".npy")])
    if not npy_files:
        print(f"No .npy files found in {in_dir}")
        return

    processed = 0
    skipped = 0

    for fname in npy_files:
        in_path = os.path.join(in_dir, fname)
        out_path = os.path.join(out_dir, fname)

        if not overwrite and os.path.exists(out_path):
            print(f"  SKIP (exists): {fname}")
            skipped += 1
            continue

        try:
            raw = np.load(in_path)
        except Exception as e:
            print(f"  SKIP (load error): {fname} — {e}")
            skipped += 1
            continue

        # Validate shape
        if raw.ndim != 2 or raw.shape[1] != 3:
            print(f"  SKIP (bad shape {raw.shape}): {fname}")
            skipped += 1
            continue

        if raw.shape[0] < 10:
            print(f"  SKIP (too short, T={raw.shape[0]}): {fname}")
            skipped += 1
            continue

        # Check for all-NaN columns
        if np.all(np.isnan(raw)):
            print(f"  SKIP (all NaN): {fname}")
            skipped += 1
            continue

        # Replace any NaN values before processing via nearest-valid interpolation
        for col in range(raw.shape[1]):
            col_data = raw[:, col]
            nans = np.isnan(col_data)
            if nans.all():
                print(f"  SKIP (column {col} all NaN): {fname}")
                skipped += 1
                break
            if nans.any():
                valid_idx = np.where(~nans)[0]
                col_data[nans] = np.interp(
                    np.where(nans)[0], valid_idx, col_data[valid_idx]
                )
                raw[:, col] = col_data
        else:
            # Only runs if inner loop did NOT break
            result = phase_anchored_interpolation(raw, total_frames=total_frames)

            # Final safety: replace any residual non-finite values
            if not np.all(np.isfinite(result)):
                print(f"  WARN (non-finite after interp, clamping): {fname}")
                result = np.nan_to_num(result, nan=0.0, posinf=180.0, neginf=0.0)

            assert result.shape == (total_frames, 3), f"Unexpected shape {result.shape}"
            assert result.dtype == np.float32

            np.save(out_path, result)
            processed += 1
            continue
        # If inner loop broke (column all NaN), skip already incremented
        continue

    print(f"\nDone: {processed} processed, {skipped} skipped out of {len(npy_files)} files.")


# ── Preview / sanity check ──────────────────────────────────
def preview(in_dir, total_frames):
    npy_files = sorted([f for f in os.listdir(in_dir) if f.endswith(".npy")])[:2]
    if not npy_files:
        print("No files to preview.")
        return

    for fname in npy_files:
        raw = np.load(os.path.join(in_dir, fname))
        print(f"\n{'='*50}")
        print(f"File: {fname}")
        print(f"  Original shape: {raw.shape}")
        print(f"  Original hole_idx (col 0 argmin): {np.argmin(raw[:, 0])}")
        print(f"  First 5 knee angles: {raw[:5, 0].round(1)}")
        print(f"  Last  5 knee angles: {raw[-5:, 0].round(1)}")

        # Run phase anchoring
        result = phase_anchored_interpolation(raw, total_frames=total_frames)
        new_hole = np.argmin(result[:, 0])
        mid = total_frames // 2
        print(f"\n  After phase-anchoring ({total_frames} frames):")
        print(f"    New hole_idx: {new_hole}  (expected ~{mid - 1} or {mid})")
        print(f"    Knee at midpoint-1: {result[mid - 1, 0]:.1f}")
        print(f"    Knee at midpoint:   {result[mid, 0]:.1f}")
        print(f"    Min knee angle:     {result[:, 0].min():.1f}")
        ok = abs(new_hole - mid) <= 2
        print(f"    Midpoint check: {'PASS' if ok else 'FAIL'}")


# ── CLI ──────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase-anchored interpolation for squat training data"
    )
    parser.add_argument(
        "--in_dir", default="training_tensors/squats/",
        help="Input directory with raw .npy files (default: training_tensors/squats/)",
    )
    parser.add_argument(
        "--out_dir", default="training_tensors/squats_phase100/",
        help="Output directory for processed files (default: training_tensors/squats_phase100/)",
    )
    parser.add_argument(
        "--frames", type=int, default=100,
        help="Total output frames (default: 100)",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Overwrite existing output files",
    )
    parser.add_argument(
        "--preview", action="store_true",
        help="Preview 1-2 files instead of batch processing",
    )

    args = parser.parse_args()

    if args.preview:
        preview(args.in_dir, args.frames)
    else:
        process_directory(args.in_dir, args.out_dir, args.frames, args.overwrite)
