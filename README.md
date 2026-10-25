# GAIT // KINETIC X — Movement Intelligence & Biomechanics Platform

[![Vercel Deployment](https://img.shields.io/badge/Vercel-Deployed-black?logo=vercel)](https://vercel.com)
[![Frontend](https://img.shields.io/badge/Frontend-Svelte_5_%2B_Vite-FF3E00?logo=svelte)](https://svelte.dev)
[![Backend](https://img.shields.io/badge/Backend-FastAPI_Python_3.12-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![MediaPipe](https://img.shields.io/badge/Pose-MediaPipe_Tasks_WASM-4285F4?logo=google)](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker)

GAIT is a high-performance biomechanics motion capture platform. It combines a state-of-the-art **Svelte 5 / Vite** sports interface (3D Three.js runner statue, GSAP animations, Lenis inertial smooth scroll) with a **FastAPI serverless backend** and **browser-side MediaPipe WebAssembly** pose tracking.

The project is structured to deploy on **Vercel as a single unified project** (frontend + serverless API on the same domain) while retaining a full local desktop hardware mode with OpenCV.

---

## 🚀 Run Commands

### 1. Run Everything Locally (One Command)

From the project root:

```bash
# Starts Python backend (port 8765) and Vite frontend (port 5173) simultaneously
npm run dev
```

> **Alternative (Full Desktop Hardware + USB Cameras + OpenCV):**
> ```bash
> python run.py
> ```

---

### 2. Frontend Only Commands

All frontend files are in the `client/` folder:

```bash
# Navigate to the frontend directory
cd client

# 1. Install dependencies
npm install

# 2. Start Vite development server (http://127.0.0.1:5173)
npm run dev

# 3. Type check & Svelte component validation
npm run check

# 4. Build optimized production bundle (outputs to client/dist)
npm run build

# 5. Preview production build locally (http://127.0.0.1:4173)
npm run preview
```

---

### 3. Backend Only Commands

The project offers two backend workflows:

#### A. Cloud / Serverless Mode (FastAPI — Same as Vercel)
Stateless ASGI backend for browser-side pose landmark analysis:

```bash
# From repository root using the virtual environment:
.venv/bin/python -m uvicorn api.index:app --host 127.0.0.1 --port 8765 --reload

# Or on Windows PowerShell:
.\.venv\Scripts\python.exe -m uvicorn api.index:app --host 127.0.0.1 --port 8765 --reload

# Or via runner script:
python scripts/dev_backend.py
```

#### B. Local Hardware Mode (OpenCV + MediaPipe Desktop Server)
Direct access to attached USB cameras and native MediaPipe models:

```bash
# From server/ directory:
cd server
python -m src.web_server

# Or inspect connected physical USB/V4L2 cameras:
python scripts/run_pose.py --list-cameras
python scripts/run_pose.py --camera usb
```

---

## ☁️ Deploying on Vercel (Single Project)

This repository deploys as **one single project** on Vercel:

1. **Push your code to GitHub**:
   ```bash
   git push origin main
   ```
2. **Import into Vercel**:
   - Go to [vercel.com/new](https://vercel.com/new) and select this repository.
   - **Root Directory**: `./` (keep at repository root).
   - **Framework Preset**: `Other` (or Vite).
   - Build settings and rewrites are managed automatically by `vercel.json`.
3. **Environment Variables** (Project Settings > Environment Variables):
   - `VITE_API_URL`: *(Leave empty — uses relative `/api/...` on the same domain, eliminating CORS issues)*.
   - `VITE_POSE_MODE`: `browser`
   - `MAX_BODY_BYTES`: `4000000`
4. **Deploy**:
   - The Svelte frontend builds into `client/dist` and is served at `/`.
   - The FastAPI backend runs under `/api/*` via `api/index.py`.
   - Client-side routes (`/gait-test`, `/report`) fallback to `/index.html` without 404s.

---

## 🏗️ Architecture & Dual Mode

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        USER BROWSER / CLIENT                           │
│  Svelte 5 · Three.js 3D Sphere · GSAP Motion · Lenis Inertial Scroll   │
│  WebRTC getUserMedia()  ──►  @mediapipe/tasks-vision (WASM/WebGL)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                  POST /api/analyze │ (Compact JSON Landmark Vectors)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      VERCEL SERVERLESS BACKEND                         │
│                    FastAPI (api/index.py - Python 3.12)                │
│                                                                        │
│   • Mathematical Gait & Biomechanics Engine (gait_analysis.py)        │
│   • Cadence, Step Symmetry, Hip/Knee Range of Motion, Trunk Lean       │
│   • Memory-safe payload validation (< 4 MB)                            │
└────────────────────────────────────────────────────────────────────────┘
```

| Feature | Cloud / Vercel Mode | Local Desktop Hardware Mode |
| :--- | :--- | :--- |
| **Hosting** | Vercel Serverless Functions (`api/index.py`) | Local Python `ThreadingHTTPServer` (`server/src/web_server.py`) |
| **Camera Capture** | Browser WebRTC (`navigator.mediaDevices`) | Native OpenCV (`cv2.VideoCapture` / `/dev/video*`) |
| **Pose Detection** | Client-side `@mediapipe/tasks-vision` (WASM) | Local MediaPipe Python desktop runtime |
| **Storage** | Client-side IndexedDB (`cloud-results.ts`) | Local CSV file recording (`server/data/sessions/`) |
| **Domain / Origin** | Unified domain (`/` and `/api/*` on same origin) | Vite proxy `5173` ──► Backend `8765` |

---

## 📂 Project Structure

```text
├── api/
│   └── index.py                           FastAPI serverless handler (exposes app)
├── client/
│   ├── src/
│   │   ├── App.svelte                     Root coordinator & page switcher
│   │   ├── sport.css                      Tailwind v4 tokens & athletic theme styles
│   │   ├── components/                    Athlete cards, 3D ball, timeline, leaderboard
│   │   ├── lib/
│   │   │   ├── api.ts                     Unified relative API client
│   │   │   ├── cloud-results.ts           IndexedDB browser persistence
│   │   │   └── pose.ts                    Client-side MediaPipe WASM detector
│   │   └── routes/
│   │       ├── gait-test/+page.svelte     Webcam discovery, preview & countdown
│   │       ├── activity/+page.svelte      Live test recording & skeleton mesh scan
│   │       └── result/[sessionId]/+page.svelte Biomechanical metrics & chart report
│   ├── package.json                       Frontend scripts and dependencies
│   └── vite.config.ts                     Vite build config with base '/' and API proxy
├── server/
│   └── src/
│       ├── gait_analysis.py               Clinical biomechanics computation engine
│       ├── web_server.py                  Local hardware API & camera service
│       └── pose_camera.py                 Desktop OpenCV capture loop
├── scripts/
│   ├── dev_backend.py                     FastAPI launcher for npm run dev
│   ├── setup.py                           Cross-platform Python + frontend installer
│   └── run_web.py                         Unified launcher for hardware mode
├── .env.example                           Documented environment variables
├── .vercelignore                          Bundle size optimizer (excludes heavy models/venv)
├── package.json                           Root scripts: dev, build, start
├── requirements.txt                       Pinned Python dependencies (FastAPI, NumPy)
├── run.py                                 One-click local desktop launcher
└── vercel.json                            Single Vercel deployment & rewrite config
```

---

## 📡 API Reference

All browser API requests include the `X-Gait-Control: 1` header.

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
# 1. Frontend validation & build
cd client
npm run check
npm run build
cd ..

# 2. Serverless API verification
.venv/bin/python -c "from api.index import app; print('App is ready:', app.title)"

# 3. Run both locally
npm run dev
```

---

*Note: GAIT is an athletic performance and movement-capture intelligence tool, not a medical device.*
