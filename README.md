# GAIT — Movement Capture Experience

GAIT is a local, privacy-conscious movement-capture project. It combines a premium Svelte/Vite sports interface with a Python HTTP backend and local MediaPipe assets. The current product flow takes an athlete from a motion-led landing page to camera selection, a full-screen 10-second movement recording, and a truthful results report.

## What was built

### Product flow

```text
Landing page
  → Start GAIT Test creates a local session
  → Choose your camera
  → Full-screen activity recording
  → 3–2–1 countdown and 10-second frame capture
  → Result report for that session
```

- **Landing page:** A high-performance sports landing experience with the GAIT identity, a lazy-loaded interactive running-athlete statue, movement stories, athlete cards, live ticker, and prominent “Start GAIT Test” calls to action.
- **Session creation:** Starting a test creates a session with `POST /api/session/create`. The session ID is retained in browser storage so the capture flow can keep its context.
- **Camera selection:** Real browser cameras are discovered using `navigator.mediaDevices.enumerateDevices()` after permission is requested. LEFT, BACK, and RIGHT slots support one to three simultaneous views, deduplicated labels, persisted rotations, per-camera quality modes, live portrait previews, and 60→30 FPS fallback.
- **Full-screen activity capture:** Selected streams are passed to the activity screen without asking for permission again. Users can select Normal Walk, Fast Walk, Run, Balance, or Toe Walk; inspect per-view body/FPS status; and rotate a view before recording.
- **Recording:** Pressing **Start Test** requests fullscreen, calls `POST /api/gait/start`, runs a GSAP 3–2–1 countdown, and captures each active view on one shared clock with `requestVideoFrameCallback` (interval fallback). A bounded shared upload queue retries transient failures without blocking video rendering.
- **Readiness and live overlay:** Before recording, live MediaPipe responses drive body-in-frame, full-body-visible, and distance checks. During capture, normalized backend keypoints draw the skeleton and a fading blue/orange footprint trail. Users can explicitly start anyway when a readiness check is unavailable.
- **Result report:** The result screen has keyboard-accessible Overview, Skeleton Replay, Charts, and Quality tabs. It polls while analysis runs, replays stored landmarks without raw video, provides an All/Left/Back/Right filter, explains unavailable metrics, includes per-view capture quality, and supports retake/delete actions.

## Design and interaction system

The interface follows a light, minimal sports direction:

- **Palette:** off-white `#F8F8F6` / `#F9F9F5`, near-black `#07171C`, and cyan accent `#00C8F5` / `#00E5FF`.
- **Typography:** Manrope variable font with tight, bold display type and restrained uppercase labels.
- **Motion:** GSAP powers entry reveals, scroll-triggered hero movement, list staggers, the recording countdown, and result counters. Lenis provides smooth scrolling on the landing page; it is intentionally not used during the full-screen camera experience.
- **3D:** Three.js renders a lightweight interactive runner statue in the hero section. It is code-split from the rest of the bundle and uses a procedural fallback until an owned/licensed GLB is supplied.
- **Usability:** The layout responds for mobile, uses visible keyboard focus, supports reduced motion, keeps the camera controls in the thumb-friendly lower area, and uses real status/error messages instead of simulated success states.

## Technology

| Layer | Implementation |
| --- | --- |
| Frontend | Svelte 5 + Vite + TypeScript |
| Motion | GSAP, ScrollTrigger, Lenis |
| 3D | Three.js |
| Styling | Component CSS, design tokens in `client/src/sport.css`, Tailwind available through Vite |
| Browser APIs | MediaDevices, `getUserMedia`, Canvas, `toBlob`, `localStorage` |
| Backend | Python `ThreadingHTTPServer`, OpenCV, MediaPipe assets |
| Transport | Fetch client in `client/src/lib/api.ts` |

This is a **Vite/Svelte single-page app**, not a SvelteKit project. The camera, activity, and result screens are Svelte components mounted by `client/src/App.svelte`; their source folders are organized as `routes/` for clarity but are not file-system URLs.

## Important files

```text
client/
├── src/App.svelte                         Landing page and flow coordinator
├── src/sport.css                          Shared GAIT visual tokens and landing styling
├── src/components/AthleteStatueScene.svelte Interactive Three.js hero runner statue
├── src/components/Tabs.svelte             Shared keyboard-accessible activity/report tabs
├── src/lib/api.ts                          Fetch-based backend client
├── src/lib/stores/session.ts               Session, activity, and shared camera-stream stores
└── src/routes/
    ├── gait-test/+page.svelte             Camera discovery and preview handoff
    ├── activity/+page.svelte              Full-screen recording and canvas overlay
    └── result/[sessionId]/+page.svelte    Animated session result report

src/
├── web_server.py                          Local API, CORS policy, sessions, and camera endpoints
├── gait_analysis.py                       Browser-frame MediaPipe processing and conservative metrics
├── pose_camera.py                         Existing local camera + MediaPipe pose/hand capture program
├── cameras.py                             Linux V4L2 and cross-platform OpenCV camera discovery
└── recorder.py                            CSV landmark recording utilities

scripts/setup.py                           Cross-platform Python, frontend, and model setup
scripts/run_web.py                         Starts the Python API and Vite UI together
```

## API used by the browser flow

All browser control requests include the `X-Gait-Control: 1` header. In development, Vite proxies `/api` calls from port `5173` to the Python API on port `8765`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/session/create` | Create a GAIT capture session |
| `GET` | `/api/cameras` | List cameras available to the local backend for diagnostics |
| `POST` | `/api/gait/start` | Mark a session as recording and save activity + active-view metadata |
| `POST` | `/api/frame/{sessionId}?view=left&seq=N&t=ms` | Receive an uploaded JPEG frame (maximum 2 MB) for a named view |
| `POST` | `/api/gait/stop/{sessionId}` | Mark the recording as captured |
| `GET` | `/api/gait/result/{sessionId}` | Return capture state, frame count, and available metrics |
| `DELETE` | `/api/session/{sessionId}` | Delete an in-memory browser capture and its landmarks |
| `GET` | `/api/status` | Inspect the existing local camera service |
| `GET` | `/api/health` | Verify the browser-frame API is reachable |
| `GET` | `/api/sessions` | List saved CSV sessions from the existing recorder |

`client/src/lib/api.ts` reads `VITE_API_URL` when provided. If it is not set, it uses relative `/api` URLs so the Vite proxy works automatically. When setting `VITE_API_URL`, point it at the running Python backend, for example `http://127.0.0.1:8765`.

## Deploying as one Vercel project

Import the repository root as a single Vercel project and keep the Vercel
project's Root Directory set to `.` (the repository root). The root
`vercel.json` declares both the Svelte frontend in `client/` and Python backend
in `server/` as services within that project. `/api/*` routes to the backend;
other paths route to the frontend. The frontend build output is `client/dist`,
matching the Vite `build.outDir` setting. Do not create separate Vercel projects
or set the Vercel project's Root Directory to `client/` or `server/`.

The deployed Python API runs as serverless functions. Browser capture sessions
are currently held in process memory and files are written to temporary
`/tmp` storage, so sessions and saved data are not durable and requests are not
guaranteed to reach the same function instance. The local hardware-camera
endpoints are also unavailable on Vercel. Use a persistent backend and
durable storage if hosted captures must survive across requests or deployments.

## Current analysis boundary

`POST /api/frame/{sessionId}` now validates and decodes each JPEG in memory, runs the local MediaPipe pose model, and returns normalized landmarks with visibility scores. During a recording, the server retains only those landmarks and timestamps. Raw frames and video are never saved.

On stop, the server reports capture quality, missing-body segments, detected step/contact peaks, cadence, step-time symmetry, left/right knee and hip motion range, mean trunk lean, and normalized balance sway when sufficient visible data exists. Every metric includes an availability flag, unit, confidence, and reason. Values remain unavailable when the signal does not meet the minimum sample/visibility rules.

Stride length and physical speed intentionally remain unavailable because a single uncalibrated 2D camera cannot provide a defensible real-world distance. Balance sway is reported in normalized frame units, not centimetres or force-plate units. The interface does not create random fallback values.

## Run locally

### Windows and Linux

Requirements:

- Python 3.12
- Node.js 22 LTS (includes npm)
- A camera for capture

Run setup once from the repository root:

```powershell
# Windows PowerShell
py -3.12 scripts/setup.py
```

```bash
# Linux
python3.12 scripts/setup.py
```

Setup creates the Python virtual environment, installs the local OpenCV GUI
build and frontend packages, and downloads the MediaPipe models into
`server/models/`. To start both services:

```powershell
# Windows PowerShell
.\.venv\Scripts\python.exe scripts\run_web.py
```

```bash
# Linux
.venv/bin/python scripts/run_web.py
```

The launcher uses the project's virtual environment and starts:

- Svelte/Vite UI: `http://127.0.0.1:5173`
- Python API: `http://127.0.0.1:8765`

Stop both services with `Ctrl+C`. The Bash wrappers in `scripts/` remain
available on Linux.

### Frontend only

```bash
cd client
npm run dev
```

The UI expects the Python API to be running if you start a GAIT test.

### Local camera and pose recorder

The browser-based capture flow uses the browser's camera permission prompt and
works on Windows and Linux without selecting a server-side camera. The
optional native pose recorder uses OpenCV: Linux discovers V4L2 devices, while
Windows uses DirectShow/Media Foundation camera indices.

List available cameras:

```powershell
.\.venv\Scripts\python.exe scripts\run_pose.py --list-cameras
```

When multiple cameras are available, select the listed numeric index on
Windows (for example `--camera 0`). On Linux, `--camera usb` selects an
identifiable external USB camera; use a device index or `/dev/videoN` for an
exact choice:

```powershell
.\.venv\Scripts\python.exe scripts\run_pose.py --camera 0
```

```bash
.venv/bin/python scripts/run_pose.py --camera usb
```

The optional local web camera service selects an external USB camera when
Linux can identify one. On Windows, a single detected camera is selected
automatically; with multiple cameras, set `GAIT_CAMERA` to the listed numeric
index before starting the app. For example, in PowerShell set
`$env:GAIT_CAMERA = "0"` before launching; in Linux use
`GAIT_CAMERA=0 .venv/bin/python scripts/run_web.py`. Camera hardware attached
to the user's computer is not directly available to the Vercel server; hosted
capture uses the browser camera and uploads frames to the API.

## Validation completed

```bash
cd client
npm run check    # Svelte + TypeScript validation
npm run build    # Production Vite bundle

cd ..
python -m py_compile server/src/web_server.py
```

Run these checks from the repository root or in the matching workspace folder;
the Windows/Linux matrix in `.github/workflows/ci.yml` runs them on both systems.

## Existing local camera recorder

The original standalone recorder remains available and is separate from the browser flow:

```bash
.venv/bin/python scripts/run_pose.py --list-cameras
.venv/bin/python scripts/run_pose.py --camera usb
```

It requests 1280×720 at 60 FPS, runs local MediaPipe pose/hand inference, and can save body landmarks to CSV in `server/data/sessions/`. It excludes face landmarks by default. See `server/src/pose_camera.py` for its capture and keyboard controls.

## Safe next development steps

1. Validate cadence and symmetry algorithms against labelled recordings from the intended camera placement and activities.
2. Add an explicit calibration or known-height workflow before enabling stride length or physical speed.
3. Persist landmark sessions only after retention, consent, and deletion policies are defined; browser sessions are currently memory-only.
4. Add downloadable reports only after the metrics and quality thresholds are validated.

GAIT is a movement-capture prototype, not a medical device or diagnosis tool.
