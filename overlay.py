"""
overlay.py — Capture a frame from the Tempest camera and composite
current weather station readings onto it.
"""

import cv2
import numpy as np
import requests
import datetime
import os
import time
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

STREAM_URL = os.getenv("STREAM_URL", "rtsps://192.168.0.1:7441/0Fbr6A8qimkATMiy?enableSrtp")
API_TOKEN = os.getenv("TEMPEST_API_TOKEN")
STATION_ID = os.getenv("TEMPEST_STATION_ID", "138504")
OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", "output/latest.jpg"))

API_URL = f"https://swd.weatherflow.com/swd/rest/observations/station/{STATION_ID}"


def fetch_observation() -> dict:
    """Fetch the latest observation from the Tempest API."""
    response = requests.get(
        API_URL,
        headers={"Authorization": f"Bearer {API_TOKEN}"},
        timeout=10
    )
    response.raise_for_status()
    return response.json()["obs"][0]


def capture_frame() -> np.ndarray:
    """Capture a single frame from the RTSPS stream."""
    cap = cv2.VideoCapture(STREAM_URL)
    if not cap.isOpened():
        raise RuntimeError("Failed to open camera stream")
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError("Failed to capture frame from stream")
    return frame


def wind_direction_compass(degrees: int) -> str:
    """Convert degrees to compass abbreviation."""
    directions = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
                  "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    index = round(degrees / 22.5) % 16
    return directions[index]


def beaufort_description(mph: float) -> str:
    """Return Beaufort scale description for wind speed."""
    scale = [
        (0, "Calm"), (3, "Light air"), (7, "Light breeze"),
        (12, "Gentle breeze"), (18, "Moderate breeze"), (24, "Fresh breeze"),
        (31, "Strong breeze"), (38, "Near gale"), (46, "Gale"),
    ]
    description = "Calm"
    for threshold, name in scale:
        if mph >= threshold:
            description = name
    return description


def draw_overlay(frame: np.ndarray, obs: dict) -> np.ndarray:
    """
    Composite weather readings onto the camera frame.
    """
    h, w = frame.shape[:2]

    # Semi-transparent dark panel across the bottom
    overlay = frame.copy()
    panel_height = 200
    cv2.rectangle(overlay, (0, h - panel_height), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    # Colours
    WHITE  = (255, 255, 255)
    GREY   = (180, 180, 180)
    YELLOW = (0, 210, 255)
    CYAN   = (255, 220, 0)

    # Font settings
    FONT   = cv2.FONT_HERSHEY_SIMPLEX
    LARGE  = 1.6
    MEDIUM = 0.9
    SMALL  = 0.68
    BOLD   = 2
    NORMAL = 1

    # Top of panel
    top = h - panel_height + 10

    # Station name and timestamp
    dt = datetime.datetime.now(datetime.timezone.utc)
    timestamp_str = dt.strftime("%H:%M UTC  %d %b %Y")
    cv2.putText(frame, "Selhurst Weather Station", (30, top + 36), FONT, MEDIUM, YELLOW, BOLD)
    cv2.putText(frame, timestamp_str, (30, top + 62), FONT, SMALL, GREY, NORMAL)

    # Divider line
    cv2.line(frame, (30, top + 74), (w - 30, top + 74), (80, 80, 80), 1)

    # Temperature block
    temp = obs["air_temperature"]
    feels = obs["feels_like"]
    cv2.putText(frame, f"{temp:.1f}C", (30, top + 130), FONT, LARGE, WHITE, BOLD)
    cv2.putText(frame, f"Feels {feels:.1f}C", (30, top + 162), FONT, SMALL, GREY, NORMAL)

    # Wind block
    wind_avg = obs["wind_avg"]
    wind_gust = obs["wind_gust"]
    wind_dir = wind_direction_compass(obs["wind_direction"])
    beaufort = beaufort_description(wind_avg)
    cv2.putText(frame, f"{wind_avg:.1f} mph {wind_dir}", (280, top + 130), FONT, MEDIUM, WHITE, BOLD)
    cv2.putText(frame, f"Gusts {wind_gust:.1f}  {beaufort}", (280, top + 162), FONT, SMALL, GREY, NORMAL)

    # Pressure block
    pressure = obs["sea_level_pressure"]
    trend = obs["pressure_trend"].capitalize()
    cv2.putText(frame, f"{pressure:.1f} mb", (560, top + 130), FONT, MEDIUM, WHITE, BOLD)
    cv2.putText(frame, f"Pressure {trend}", (560, top + 162), FONT, SMALL, GREY, NORMAL)

    # UV and solar block
    uv = obs["uv"]
    solar = obs["solar_radiation"]
    cv2.putText(frame, f"UV {uv:.1f}", (820, top + 130), FONT, MEDIUM, CYAN, BOLD)
    cv2.putText(frame, f"{solar:.0f} W/m2", (820, top + 162), FONT, SMALL, GREY, NORMAL)

    # Humidity, dew point and rain
    rh = obs["relative_humidity"]
    dew = obs["dew_point"]
    rain_today = obs["precip_accum_local_day"]
    cv2.putText(frame, f"RH {rh:.0f}%  Dew {dew:.1f}C", (1080, top + 130), FONT, MEDIUM, WHITE, BOLD)
    cv2.putText(frame, f"Rain today: {rain_today:.1f} mm", (1080, top + 162), FONT, SMALL, GREY, NORMAL)

    return frame

def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    interval = int(os.getenv("CAPTURE_INTERVAL_SECONDS", 600))
    print(f"Starting camera overlay. Capturing every {interval} seconds.")

    while True:
        try:
            print("Fetching observation...")
            obs = fetch_observation()

            print("Capturing frame...")
            frame = capture_frame()

            print("Drawing overlay...")
            annotated = draw_overlay(frame, obs)

            cv2.imwrite(str(OUTPUT_PATH), annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
            print(f"Saved to {OUTPUT_PATH}")
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(interval)
    

if __name__ == "__main__":
    main()
