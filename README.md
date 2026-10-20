# G3-V2 — Single-Camera Gait Data Recorder

## Live web camera and ML

Run `bash scripts/run_web.sh`, then open `http://127.0.0.1:5173`.
The launcher starts the Python API and Svelte UI together. Stop it with Ctrl+C.
Camera opens the first readable external USB capture device and automatically
loads the existing pose and hand models. If several external cameras are attached,
disconnect the ones you do not intend to use. Built-in camera names are excluded
using the existing name heuristics; check the displayed camera name before recording.
Start in Test Studio also records a 60-second CSV session.
Stop saves early and releases the camera; navigating away stops capture too.
After a timed recording, preview stays live until Stop. Use one browser tab.
If the browser stops checking status for 15 seconds, capture saves and stops.
CSV output remains in `data/sessions/` and excludes face landmarks.
Camera disconnects and model errors are shown in Test Studio; reconnect and retry.
This is a local development service, bound to loopback, not an internet deployment.
Dashboard and session history read saved recordings through `/api/sessions`.
Report tabs show actual frame counts, landmark counts, and the interval between
the first and last captured sample. This sample span is not the total test duration.
Joint angles and symmetry remain explicitly uncalculated; coaching is not active.
The history supports search, status filtering, session reports, and CSV downloads.
The guided studio opens preview with Camera and records with Start. Dashboard's
Begin button takes you to setup first. Expandable help explains readiness and data.
Restart the Python backend after updating to enable the new session endpoints.
Live ML means landmark tracking, not a trained gait diagnosis classifier.

This is a small, separate MediaPipe project for one USB camera. It does not
modify or replace an existing three-camera project.

## Folder roles

```text
.
├── models/               downloaded MediaPipe pose model (not stored in Git)
├── scripts/
│   ├── setup.sh          creates the virtual environment and installs packages
│   └── run_pose.sh       starts the pose camera program
├── src/
│   ├── check_setup.py    checks versions, model, and camera 0
│   └── pose_camera.py    reads one camera and draws body landmarks
├── .gitignore            keeps generated files out of Git
└── requirements.txt      exact Python package versions
```

## Step 1: Connect the camera

Connect one USB camera. Check that Linux can see it:

```bash
v4l2-ctl --list-devices
```

The program uses camera index `0`, normally `/dev/video0`.

## Step 2: Install in an isolated environment

From this project folder:

```bash
chmod +x scripts/setup.sh scripts/run_pose.sh
./scripts/setup.sh
```

The packages are installed only inside `.venv`. They will not change the
packages used by the existing three-camera project.

## Step 3: Verify everything

```bash
.venv/bin/python -m src.check_setup
```

Expected output includes MediaPipe `0.10.35`, the OpenCV version, `Pose model:
ready`, and the external USB camera resolution. To check the built-in camera
instead, add `--camera built-in`.

## Step 4: Run pose detection and recording

List the cameras first:

```bash
./scripts/run_pose.sh --list-cameras


Use the external USB camera (default):

```bash
./scripts/run_pose.sh
# Same as: ./scripts/run_pose.sh --camera usb
```

Use the laptop's built-in camera only when requested:

```bash
./scripts/run_pose.sh --camera built-in
```

If Linux reports several camera devices, select the exact one shown by the
list command:

```bash
./scripts/run_pose.sh --camera /dev/video2
```

The camera requests 1280x720 at 60 FPS using MJPEG and opens in fullscreen.
The image is cropped to fill the complete display without white borders. The
bottom-left overlay separately shows display, pose, hand, and camera FPS. The
default `fast` profile runs pose and hand inference in independent background
workers on a 640x360 ML copy while keeping the visible camera image at 720p.
Body inference has priority. Hand detection searches at a lower rate while no
hand is visible, then increases its tracking rate automatically when a hand is
found. This prevents hand detection from continuously reducing body FPS.
Stand where your full body is visible. The
body tracker excludes all face landmarks and smooths small landmark movement
to reduce jitter. Showing either hand automatically enables hand landmarks
with thin lines and small dots.

Press `Q` or `Esc` to stop. Press `F` to switch between fullscreen and a
normal window.

### Record gait landmarks to CSV

Start the app with a session name and activity label:

```bash
./scripts/run_pose.sh --camera usb \
  --session-name "participant-01-walk-01" \
  --activity walking
```

Recording controls inside the camera window:

- `R`: start recording
- `P`: pause or resume recording
- `S`: save and stop recording
- `Q` or `Esc`: safely save an active recording and exit

CSV files are saved under `data/sessions/`. Each row contains the session ID,
session name, activity, frame index, UTC timestamp, active elapsed time, model
timestamp, landmark index/name, normalized `x`, `y`, and `z`, visibility, and
presence confidence.

The privacy-focused default saves the 22 body landmarks numbered 11–32 and
does not save MediaPipe's 11 face/head landmarks. If a study genuinely needs
all 33 landmarks, start with `--include-face`:

```bash
./scripts/run_pose.sh --camera usb --include-face
```

Only new pose inference results are recorded. Repeated display frames are not
duplicated in the CSV.

For the slower full pose model, use:

```bash
./scripts/run_pose.sh --camera usb --quality accurate
```

This version uses the CPU. A GPU is not required.

## Simple version-control workflow

After a working change:

```bash
git status
git add .
git commit -m "Describe the working change"
```

Create a commit only after testing. This gives you a safe point to return to.

## Gait ML roadmap after Version 2

1. Normalize recorded coordinates so distance from the camera affects them less.
2. Calculate gait features such as knee angle, hip angle, step timing, and
   left-right symmetry.
3. Record labelled walking examples for the gait classes you actually need.
4. Train a small CPU-friendly model, starting with Random Forest or XGBoost.
5. Test by person: do not put frames from one person in both training and test
   sets.
6. Add live prediction only after offline test results are reliable.

Do not train a model directly on camera images yet; landmarks are much simpler
and need far less data and CPU.

## AURA Motion frontend

The Svelte 5 interface is in `frontend/`. It includes a cream-and-red glass
design, responsive dashboard, guided live camera capture, searchable session
history, keyboard-accessible report tabs, and expandable help. Session summaries
come from saved CSVs. Joint angles and symmetry remain explicitly uncalculated.
Use `bash scripts/run_web.sh` to start both the frontend and Python API together.
For frontend-only development, run:

```bash
cd frontend
npm install
npm run dev
```

Validation commands:

```bash
npm run check
npm run build
```
