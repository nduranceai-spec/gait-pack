import type { PoseKeypoint } from './api';

const ANALYSIS_INDICES = new Set([11, 12, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]);
type Delegate = 'GPU' | 'CPU';
type PoseLandmarker = { detectForVideo(input: CanvasImageSource, timestamp: number): { landmarks: Array<Array<{ x: number; y: number; z: number; visibility?: number }>> }; close(): void };

let landmarker: Promise<PoseLandmarker> | null = null;
let activeDelegate: Delegate = 'GPU';
let statusMessage = '';

export function poseStatus() { return statusMessage; }

async function create(delegate: Delegate): Promise<PoseLandmarker> {
  const vision = await import('@mediapipe/tasks-vision');
  const files = await vision.FilesetResolver.forVisionTasks('/mediapipe');
  return vision.PoseLandmarker.createFromOptions(files, {
    baseOptions: { modelAssetPath: '/mediapipe/pose_landmarker_lite.task', delegate },
    runningMode: 'VIDEO', numPoses: 1,
    minPoseDetectionConfidence: .55, minPosePresenceConfidence: .55, minTrackingConfidence: .55,
  }) as unknown as PoseLandmarker;
}

async function detector() {
  if (!landmarker) landmarker = create('GPU').catch(async () => {
    activeDelegate = 'CPU';
    statusMessage = 'GPU pose processing is unavailable; using the CPU fallback.';
    return create('CPU');
  });
  return landmarker;
}

export async function detectPose(video: HTMLVideoElement, timestamp = performance.now()): Promise<PoseKeypoint[]> {
  if (!video.videoWidth || !video.videoHeight) return [];
  const canvas = document.createElement('canvas');
  const left = Math.round(video.videoWidth * .10), top = Math.round(video.videoHeight * .03);
  const width = Math.round(video.videoWidth * .80), height = Math.round(video.videoHeight * .95);
  canvas.width = width; canvas.height = height;
  canvas.getContext('2d')?.drawImage(video, left, top, width, height, 0, 0, width, height);
  const result = (await detector()).detectForVideo(canvas, timestamp);
  const points = result.landmarks?.[0] ?? [];
  return points.flatMap((point, index) => ANALYSIS_INDICES.has(index) ? [{ index, x: Math.round((.10 + point.x * .80) * 1000) / 1000, y: Math.round((.03 + point.y * .95) * 1000) / 1000, z: Math.round(point.z * 1000) / 1000, visibility: Math.round((point.visibility ?? 0) * 1000) / 1000 }] : []);
}

export class PoseTracker {
  private frame = 0;
  private last = 0;
  private running = false;
  constructor(private video: HTMLVideoElement, private onFrame: (points: PoseKeypoint[], timestamp: number) => void, private onError: (message: string) => void = () => {}) {}
  start() { this.running = true; const loop = async (now: number) => { if (!this.running) return; if (now - this.last >= 66) { this.last = now; try { this.onFrame(await detectPose(this.video, now), now); } catch (error) { this.onError(error instanceof Error ? error.message : 'Pose detection failed.'); } } this.frame = requestAnimationFrame(loop); }; this.frame = requestAnimationFrame(loop); }
  stop() { this.running = false; cancelAnimationFrame(this.frame); }
}

export function disposePose() { landmarker?.then((item) => item.close()); landmarker = null; }
export { activeDelegate };
