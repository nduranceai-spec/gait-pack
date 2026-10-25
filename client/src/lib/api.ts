import { listCloudResults, readCloudResult, removeCloudResult } from './cloud-results';

const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
export type PoseMode = 'browser' | 'server';
let detectedPoseMode: Promise<PoseMode> | null = null;

export interface GaitSession {
  sessionId: string;
  timestamp: string;
}

export interface BackendCamera {
  id: string;
  label: string;
  node?: string;
  connection?: string;
  modes?: Array<{ format: string; resolution: string; fps: number }>;
}

export interface PoseKeypoint {
  index: number;
  x: number;
  y: number;
  z: number;
  visibility: number;
}

export type CameraView = 'left' | 'back' | 'right';
export interface GaitViewMetadata {
  view: CameraView;
  cameraLabel: string;
  rotation: number;
  width: number | null;
  height: number | null;
  fps: number | null;
}

export interface PersonDetails {
  name: string;
  age: string;
  height: string;
  weight: string;
}

export interface ViewCaptureQuality {
  view: CameraView;
  cameraLabel: string;
  rotation: number;
  width: number | null;
  height: number | null;
  fps: number | null;
  sent: number;
  received: number;
  detected: number;
  detectionRate: number;
  gaps: Array<{ start: number; end: number }>;
  state: string;
}

export interface MetricValue {
  value: number | null;
  unit: string;
  confidence: number;
  available: boolean;
  reason: string;
  sourceViews?: CameraView[];
}

export interface GaitMetrics {
  steps: MetricValue;
  cadence: MetricValue;
  stepTimeSymmetry: MetricValue;
  leftKneeRange: MetricValue;
  rightKneeRange: MetricValue;
  leftHipRange: MetricValue;
  rightHipRange: MetricValue;
  trunkLean: MetricValue;
  swayPath: MetricValue;
  swayArea: MetricValue;
  strideLength: MetricValue;
  speed: MetricValue;
}

export interface LandmarkFrame {
  t: number;
  timestamp: string;
  keypoints: PoseKeypoint[];
}

export interface CompactFrame { t: number; timestamp: string; seq: number; keypoints: PoseKeypoint[]; }
export interface AnalyzeViewPayload { sessionId: string; activityType: string; person: PersonDetails; durationSec: 30 | 60 | 120; view: CameraView; metadata: GaitViewMetadata; frames: CompactFrame[]; sentCount: number; }

export interface TimeSeriesPoint {
  t: number;
  leftKnee?: number;
  rightKnee?: number;
  leftHip?: number;
  rightHip?: number;
  trunkLean?: number;
  swayX?: number;
  swayY?: number;
  leftHeelY?: number;
  rightHeelY?: number;
  stepEvent?: 'left' | 'right' | null;
}

export interface GaitResult {
  sessionId: string;
  state: 'created' | 'recording' | 'processing' | 'ready' | 'failed' | 'captured' | 'insufficient-data';
  activity: string;
  frameCount: number;
  framesReceived: number;
  durationSec: number;
  detectedFrames: number;
  timestamp: string;
  person?: PersonDetails;
  metrics: GaitMetrics;
  quality: {
    score: number;
    confidence: number;
    fullBodyRatio: number;
    feetVisibleRatio: number;
    notes: string[];
    missingSegments: Array<{ start: number; end: number }>;
  };
  timeSeries: TimeSeriesPoint[];
  landmarkTimeline: LandmarkFrame[];
  camera: { name: string; fps: number | null };
  views?: ViewCaptureQuality[];
  landmarksByView?: Partial<Record<CameraView, LandmarkFrame[]>>;
  message?: string;
}

export interface FrameResponse {
  accepted: boolean;
  framesReceived: number;
  bodyDetected?: boolean;
  keypoints?: PoseKeypoint[];
  timestamp?: string;
  elapsedSec?: number;
  view?: CameraView;
  seq?: number;
  detectedCount?: number;
}

export interface SessionHistoryItem {
  sessionId?: string;
  name: string;
  activity: string;
  date: string | null;
  frames: number;
  status: string;
  source?: string;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { 'X-Gait-Control': '1', ...(init.headers || {}) },
  });
  const payload = await response.json().catch(() => null) as { error?: string } | T | null;
  if (!response.ok) throw new Error((payload as { error?: string } | null)?.error || `Request failed (${response.status}).`);
  return payload as T;
}

export function createSession(): Promise<GaitSession> {
  return request<GaitSession>('/api/session/create', { method: 'POST' });
}

export function getPoseMode(): Promise<PoseMode> {
  const override = import.meta.env.VITE_POSE_MODE as PoseMode | undefined;
  if (override === 'browser' || override === 'server') return Promise.resolve(override);
  if (!detectedPoseMode) detectedPoseMode = request<{ hardware_mode: boolean }>('/api/hardware').then((value) => value.hardware_mode ? 'server' : 'browser').catch(() => 'browser');
  return detectedPoseMode;
}

function compact(frame: CompactFrame): [number, string, number, number[][]] {
  const indices = new Set([11, 12, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]);
  const round = (value: number) => Math.round(value * 1000) / 1000;
  return [round(frame.t), frame.timestamp, frame.seq, frame.keypoints.filter((point) => indices.has(point.index)).map((point) => [point.index, round(point.x), round(point.y), round(point.z), round(point.visibility)])];
}

export async function analyzeView(payload: AnalyzeViewPayload): Promise<GaitResult> {
  let frames = payload.frames;
  let body = JSON.stringify({ ...payload, frames: frames.map(compact) });
  while (new Blob([body]).size > 3_500_000 && frames.length > 2) { frames = frames.filter((_, index) => index % 2 === 0); body = JSON.stringify({ ...payload, frames: frames.map(compact) }); }
  if (new Blob([body]).size > 3_500_000) throw new Error('Pose data for this view is too large to upload. Shorten the test or reduce the sample rate.');
  const response = await fetch(`${API_URL}/api/analyze`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Gait-Control': '1' }, body });
  const value = await response.json().catch(() => null) as { error?: string; detail?: string } | GaitResult | null;
  if (!response.ok) throw new Error((value as { error?: string; detail?: string } | null)?.error || (value as { detail?: string } | null)?.detail || `Analysis failed (${response.status}).`);
  return value as GaitResult;
}

export function getCameras(): Promise<BackendCamera[]> {
  return request<BackendCamera[]>('/api/cameras');
}

export function startGait(
  sessionId: string,
  activityType: string,
  camera?: { name: string; fps: number | null },
  views?: GaitViewMetadata[],
  person?: PersonDetails,
  durationSec?: number,
): Promise<{ sessionId: string; state: string }> {
  return request('/api/gait/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sessionId, activityType, camera, views, person, durationSec }),
  });
}

export function uploadFrame(sessionId: string, frame: Blob, options: { view?: CameraView; seq?: number; timestampMs?: number } = {}): Promise<FrameResponse> {
  const params = new URLSearchParams();
  if (options.view) params.set('view', options.view);
  if (typeof options.seq === 'number') params.set('seq', String(options.seq));
  if (typeof options.timestampMs === 'number') params.set('t', String(options.timestampMs));
  const suffix = params.size ? `?${params}` : '';
  return request<FrameResponse>(`/api/frame/${encodeURIComponent(sessionId)}${suffix}`, {
    method: 'POST',
    headers: { 'Content-Type': 'image/jpeg' },
    body: frame,
  });
}

export async function getGaitResult(sessionId: string): Promise<GaitResult> {
  if (await getPoseMode() === 'browser') { const result = await readCloudResult(sessionId); if (!result) throw new Error('This browser does not have the saved GAIT result.'); return result; }
  return request<GaitResult>(`/api/gait/result/${encodeURIComponent(sessionId)}`);
}

export function stopGait(sessionId: string, sentCounts?: Partial<Record<CameraView, number>>): Promise<{ sessionId: string; state: string }> {
  return request(`/api/gait/stop/${encodeURIComponent(sessionId)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sentCounts }),
  });
}

export function getHealth(): Promise<{ state: string }> { return request('/api/health'); }

export async function deleteSession(sessionId: string): Promise<{ sessionId: string; deleted: boolean }> {
  if (await getPoseMode() === 'browser') { await removeCloudResult(sessionId); return { sessionId, deleted: true }; }
  return request(`/api/session/${encodeURIComponent(sessionId)}`, { method: 'DELETE' });
}

export async function getSessionHistory(): Promise<SessionHistoryItem[]> {
  if (await getPoseMode() === 'browser') return listCloudResults();
  return request<SessionHistoryItem[]>('/api/sessions');
}
