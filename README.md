# GAIT // KINETIC X — Movement Intelligence & Biomechanics Platform

[![Vercel Deployment](https://img.shields.io/badge/Vercel-Deployed-black?logo=vercel)](https://vercel.com)
[![Frontend](https://img.shields.io/badge/Frontend-Svelte_5_%2B_Vite-FF3E00?logo=svelte)](https://svelte.dev)
[![Backend](https://img.shields.io/badge/Backend-FastAPI_Python_3.12-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![MediaPipe](https://img.shields.io/badge/Pose-MediaPipe_Tasks_WASM-4285F4?logo=google)](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker)

GAIT is a high-performance biomechanics motion capture platform. It combines a state-of-the-art **Svelte 5 / Vite** sports interface (3D Three.js runner statue, GSAP animations, Lenis inertial smooth scroll) with a **FastAPI backend** and **browser-side MediaPipe WebAssembly** pose tracking.

The project is cleanly divided into two self-contained directories: **`client/`** (frontend) and **`server/`** (backend & biomechanics engine).

---

## 📂 Project Structure

```text
├── client/                                Frontend Application (Svelte 5 + Vite)
│   ├── .env.example                       Client environment variable definitions
│   ├── index.html                         HTML root template
│   ├── package.json                       Frontend scripts, UI & animation dependencies
│   ├── public/                            Static assets & MediaPipe WASM runtime
│   ├── src/
│   │   ├── App.svelte                     Root coordinator & page switcher
│   │   ├── sport.css                      Tailwind v4 tokens & athletic styling
│   │   ├── components/                    Athlete cards, 3D ball, timeline, leaderboard
│   │   ├── lib/
│   │   │   ├── api.ts                     Unified relative API client
│   │   │   ├── cloud-results.ts           IndexedDB browser persistence
│   │   │   └── pose.ts                    Client-side MediaPipe WASM detector
│   │   └── routes/
│   │       ├── gait-test/+page.svelte     Webcam discovery, preview & countdown
│   │       ├── activity/+page.svelte      Live test recording & skeleton mesh scan
│   │       └── result/[sessionId]/+page.svelte Biomechanical metrics & chart report
│   ├── tsconfig.json                      TypeScript configuration
│   └── vite.config.ts                     Vite build config with base '/' and API proxy
│
├── server/                                Backend Application (FastAPI + Biomechanics Engine)
│   ├── .env.example                       Server environment variable definitions
│   ├── .python-version                    Target Python runtime (3.12)
│   ├── pyproject.toml                     Package configuration & build metadata
│   ├── requirements.txt                   FastAPI, MediaPipe, OpenCV headless, NumPy
│   ├── run.py                             Single runnable script for both backend & frontend
│   ├── index.py                           FastAPI application entrypoint
│   ├── api/
│   │   └── index.py                       Stateless FastAPI serverless handler
│   ├── scripts/
│   │   ├── dev_backend.py                 FastAPI dev server runner with hot reload
│   │   ├── run_web.py                     Unified launcher for hardware mode
│   │   ├── run_pose.py                    CLI pose landmarker on camera stream
│   │   └── setup.py                       Dependency installer & model downloader
│   ├── src/
│   │   ├── gait_analysis.py               Clinical biomechanics computation engine
│   │   ├── web_server.py                  Local hardware API & camera service
│   │   ├── cameras.py                     Hardware USB / V4L2 camera discovery
│   │   ├── hardware_pose.py               MediaPipe pose extraction pipeline
│   │   ├── pose_camera.py                 Desktop OpenCV capture loop
│   │   ├── recorder.py                    Session frame & keypoint recorder
│   │   └── sessions.py                    Session persistence manager
│   ├── models/                            Downloaded MediaPipe .task models
│   └── tests/                             Backend unit & camera discovery tests
│
├── vercel.json                            Vercel monorepo configuration (routes client & server)
├── .vercelignore                          Deployment bundle exclusions
├── .gitignore                             Standard Git ignore rules
└── README.md                              Platform documentation
```

---

## 🚀 Quick Start

### 1. Unified Launcher (Frontend + Backend)

Run the full platform with a single command from the project root:

```bash
# Starts Python backend (port 8765) and Vite frontend (port 5173) simultaneously:
python server/run.py
```

---

### 2. Frontend Development (`client/`)

All frontend code and dependencies reside in `client/`:

```bash
cd client

# 1. Install frontend dependencies
npm install

# 2. Start Vite development server (http://127.0.0.1:5173)
npm run dev

# 3. Type check & Svelte validation
npm run check

# 4. Build optimized production bundle
npm run build

# 5. Preview production build locally
npm run preview
```

---

### 3. Backend Development (`server/`)

All backend code, dependencies, and APIs reside in `server/`:

```bash
cd server

# 1. Install dependencies
pip install -r requirements.txt

# 2. Run FastAPI development server with hot reload (http://127.0.0.1:8765)
python -m uvicorn api.index:app --host 127.0.0.1 --port 8765 --reload

# Or use the convenience runner:
python scripts/dev_backend.py
```

#### Optional: Local Hardware Mode (OpenCV + USB Cameras)
For testing physical USB / V4L2 cameras directly with OpenCV:

```bash
cd server
python -m src.web_server

# Camera inspection tools:
python scripts/run_pose.py --list-cameras
python scripts/run_pose.py --camera usb
```

---

## ☁️ Deploying on Vercel

This repository deploys as **one single project** on Vercel using `vercel.json` services configuration:

1. **Import into Vercel**:
   - Go to [vercel.com/new](https://vercel.com/new) and select this repository.
   - **Root Directory**: `./` (keep at repository root).
   - Vercel automatically maps `client/` to the Vite frontend and `server/` to the FastAPI backend via `vercel.json`.
2. **Environment Variables** (Project Settings > Environment Variables):
   - `VITE_API_URL`: *(Leave empty — uses relative `/api/...` on the same domain, eliminating CORS issues)*.
   - `VITE_POSE_MODE`: `browser`
   - `MAX_BODY_BYTES`: `4000000`
3. **Deploy**:
   - Frontend is compiled and served at `/`.
   - FastAPI backend handles all `/api/*` endpoints.

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Liveness check returning `{"status": "ok", "state": "ready"}` |
| `GET` | `/api/hardware` | Returns `{"hardware_mode": false}` on cloud, `true` on local server |
| `POST` | `/api/session/create` | Generates a new unique `sessionId` |
| `POST` | `/api/analyze` | Computes cadence, range of motion, symmetry, and quality metrics |
| `GET` | `/api/cameras` | Lists attached USB cameras (hardware mode diagnostics) |
| `GET` | `/api/sessions` | Lists recorded sessions (IndexedDB on cloud, CSV locally) |
| `DELETE`| `/api/session/{sessionId}` | Deletes a session and associated data |

---

## 🔬 Biomechanical Metrics Extracted

* **Temporal Metrics:** Cadence (steps/min), step time, bilateral step time symmetry ratio.
* **Kinematics:** Left and right knee flexion/extension range, left and right hip flexion range.
* **Postural Stability:** Mean trunk lean angle, normalized center-of-mass balance sway path & sway area.
* **Truthful Boundaries:** Speed and absolute stride length remain unavailable on single 2D uncalibrated cameras to prevent arbitrary/fabricated values.

---

## 🛠️ Verification & Quality Checks

Run these commands to verify complete repository health:

```bash
# 1. Frontend check & build
npm --prefix client run check
npm --prefix client run build

# 2. Server API & unit tests
python -m unittest discover -s server/tests -v
python -m compileall -q server/scripts server/src server/api

# 3. Verify server entrypoint
python -c "import sys; sys.path.insert(0, 'server'); from api.index import app; print('App ready:', app.title)"
```

---

*Note: GAIT is an athletic performance and movement-capture intelligence tool, not a medical device.*
