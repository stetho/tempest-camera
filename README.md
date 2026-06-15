# Tempest Camera

A Python service that captures frames from a WeatherFlow Tempest camera and
composites live weather station readings onto the image as an overlay.

Runs continuously in Docker, updating the annotated image every 10 minutes.
The output image is served by [tempest-dashboard](https://github.com/stetho/tempest-dashboard)
and displayed on the Camera tab at [tempest.23wwc.cloud](https://tempest.23wwc.cloud).

![Camera overlay example](docs/example.jpg)

## Features

- Connects to the Tempest RTSPS camera stream via OpenCV
- Fetches live conditions from the Tempest REST API
- Composites a semi-transparent overlay onto the bottom of the frame showing:
  - Temperature and feels like
  - Wind speed, direction and Beaufort description
  - Sea level pressure and trend
  - UV index and solar radiation
  - Relative humidity, dew point and daily rainfall
- Saves the annotated image to a shared Docker volume
- Runs on a configurable interval (default 10 minutes)
- Handles errors gracefully and continues running

## Requirements

- Docker and Docker Compose
- A WeatherFlow Tempest weather station with camera
- Access to the camera RTSPS stream on your local network
- A Tempest API token (free from [tempestwx.com](https://tempestwx.com))

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/stetho/tempest-camera.git
cd tempest-camera
```

**2. Create your `.env` file**

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
TEMPEST_API_TOKEN=your_token_here
TEMPEST_STATION_ID=your_station_id
STREAM_URL=rtsps://your_camera_ip:7441/your_stream_key?enableSrtp
OUTPUT_PATH=output/latest.jpg
CAPTURE_INTERVAL_SECONDS=600
```

**3. Start the container**

```bash
docker compose up -d --build
```

**4. Verify it's working**

```bash
docker compose logs -f
```

You should see:

```
Starting camera overlay. Capturing every 600 seconds.

Fetching observation...

Capturing frame...

Drawing overlay...

Saved to output/latest.jpg
```
## Configuration

| Variable | Description | Default |
|---|---|---|
| `TEMPEST_API_TOKEN` | Your Tempest API bearer token | Required |
| `TEMPEST_STATION_ID` | Your station ID | Required |
| `STREAM_URL` | Full RTSPS URL to your camera stream | Required |
| `OUTPUT_PATH` | Where to save the annotated image | `output/latest.jpg` |
| `CAPTURE_INTERVAL_SECONDS` | How often to capture in seconds | `600` |

## Integration with tempest-dashboard

The dashboard mounts the `output/` directory as a Docker volume and serves
the latest image at `/camera/latest`. In your dashboard `docker-compose.yml`:

```yaml
volumes:
  - /data/tempest-logger/data:/data
  - /data/tempest-camera/output:/camera
```

## Part of a Larger Project

| Phase | Repo | Description | Status |
|---|---|---|---|
| 1 | `tempest-logger` | Data collection service | ✅ Complete |
| 2 | `tempest-analytics` | Derived calculations library | ✅ Complete |
| 3 | `tempest-dashboard` | Web visualisation | ✅ Complete |
| 4 | `tempest-camera` | Camera overlay and timelapse | 🚧 In progress |
| 5 | `tempest-alerts` | Threshold alerting service (Go) | 📋 Planned |

## License

MIT
