"""
timelapse.py — Stitch a day's worth of captured frames into a timelapse video.

Run this once per day, either manually or via a scheduled task.
Produces one MP4 per day in the output/timelapse/ directory.
Cleans up processed frames to manage disk space.
"""

import cv2
import os
import sys
import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", "output/latest.jpg"))
FRAMES_DIR = OUTPUT_PATH.parent / "frames"
TIMELAPSE_DIR = OUTPUT_PATH.parent / "timelapse"
FPS = int(os.getenv("TIMELAPSE_FPS", 10))
KEEP_FRAMES_DAYS = int(os.getenv("KEEP_FRAMES_DAYS", 2))


def get_frames_for_date(date: datetime.date) -> list[Path]:
    """
    Return all saved frames for a given date, sorted chronologically.

    Args:
        date: The date to get frames for.

    Returns:
        List of Path objects sorted oldest to newest.
    """
    if not FRAMES_DIR.exists():
        return []

    prefix = date.strftime("%Y%m%d_")
    frames = sorted([
        f for f in FRAMES_DIR.iterdir()
        if f.name.startswith(prefix) and f.suffix == ".jpg"
    ])
    return frames


def generate_timelapse(date: datetime.date) -> Path | None:
    """
    Generate a timelapse video for a given date.

    Args:
        date: The date to generate a timelapse for.

    Returns:
        Path to the generated video, or None if no frames found.
    """
    frames = get_frames_for_date(date)

    if not frames:
        print(f"No frames found for {date}")
        return None

    print(f"Found {len(frames)} frames for {date}")

    # Read first frame to get dimensions
    first = cv2.imread(str(frames[0]))
    if first is None:
        print(f"Could not read first frame: {frames[0]}")
        return None

    h, w = first.shape[:2]

    TIMELAPSE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = TIMELAPSE_DIR / f"{date.strftime('%Y%m%d')}.mp4"

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, FPS, (w, h))

    for frame_path in frames:
        frame = cv2.imread(str(frame_path))
        if frame is not None:
            writer.write(frame)

    writer.release()
    print(f"Timelapse saved to {output_path}")
    print(f"Duration: {len(frames) / FPS:.1f} seconds at {FPS} fps")
    return output_path


def cleanup_old_frames(keep_days: int = 2):
    """
    Delete frames older than keep_days to manage disk space.

    Args:
        keep_days: Number of days of frames to keep.
    """
    if not FRAMES_DIR.exists():
        return

    cutoff = datetime.date.today() - datetime.timedelta(days=keep_days)
    deleted = 0

    for frame in FRAMES_DIR.iterdir():
        if frame.suffix != ".jpg":
            continue
        try:
            frame_date_str = frame.name[:8]
            frame_date = datetime.datetime.strptime(frame_date_str, "%Y%m%d").date()
            if frame_date < cutoff:
                frame.unlink()
                deleted += 1
        except (ValueError, IndexError):
            pass

    if deleted:
        print(f"Cleaned up {deleted} frames older than {cutoff}")


def main():
    # Default to yesterday — run this script at the start of each new day
    if len(sys.argv) > 1:
        target_date = datetime.date.fromisoformat(sys.argv[1])
    else:
        target_date = datetime.date.today() - datetime.timedelta(days=1)

    print(f"Generating timelapse for {target_date}")
    generate_timelapse(target_date)
    cleanup_old_frames(KEEP_FRAMES_DAYS)


if __name__ == "__main__":
    main()
