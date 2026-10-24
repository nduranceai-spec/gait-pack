import { writable } from 'svelte/store';

const storageKey = 'gait.session-id';
const activityStorageKey = 'gait.activity-type';
const durationStorageKey = 'gait.test-duration';
const initialValue = typeof localStorage === 'undefined' ? null : localStorage.getItem(storageKey);
const initialActivity = typeof localStorage === 'undefined' ? 'Normal Walk' : localStorage.getItem(activityStorageKey) || 'Normal Walk';
const savedDuration = typeof localStorage === 'undefined' ? 30 : Number(localStorage.getItem(durationStorageKey) || 30);
export type ActivityType = 'Normal Walk' | 'Fast Walk' | 'Run' | 'Balance' | 'Toe Walk';
export interface CameraMeta {
  label: string;
  mirrored: boolean;
  facingMode: string;
  fps: number | null;
}

export type CameraView = 'left' | 'back' | 'right';
export const cameraViews: CameraView[] = ['left', 'back', 'right'];
export type CameraQuality = 'auto' | '720p30' | '480p30' | '360p15';

export interface CaptureView {
  view: CameraView;
  deviceId: string;
  label: string;
  stream: MediaStream;
  rotation: number;
  width: number | null;
  height: number | null;
  fps: number | null;
  mirrored: boolean;
}

export interface SavedCameraAssignment {
  deviceId: string | null;
  rotation: number;
  quality: CameraQuality;
}

const cameraAssignmentKey = 'gait.camera-assignments';
const emptyAssignments = (): Record<CameraView, SavedCameraAssignment> => ({
  left: { deviceId: null, rotation: 0, quality: 'auto' },
  back: { deviceId: null, rotation: 0, quality: 'auto' },
  right: { deviceId: null, rotation: 0, quality: 'auto' },
});

function savedAssignments(): Record<CameraView, SavedCameraAssignment> {
  if (typeof localStorage === 'undefined') return emptyAssignments();
  try {
    const parsed = JSON.parse(localStorage.getItem(cameraAssignmentKey) || '{}') as Partial<Record<CameraView, SavedCameraAssignment>>;
    const defaults = emptyAssignments();
    return cameraViews.reduce((value, view) => {
      const saved = parsed[view];
      value[view] = {
        deviceId: typeof saved?.deviceId === 'string' ? saved.deviceId : null,
        rotation: [0, 90, 180, 270].includes(saved?.rotation ?? 0) ? saved!.rotation : 0,
        quality: saved?.quality === '720p30' || saved?.quality === '480p30' || saved?.quality === '360p15' ? saved.quality : 'auto',
      };
      return value;
    }, defaults);
  } catch { return emptyAssignments(); }
}

function createSessionStore() {
  const { subscribe, set } = writable<string | null>(initialValue);
  return {
    subscribe,
    set(sessionId: string | null) {
      if (typeof localStorage !== 'undefined') {
        if (sessionId) localStorage.setItem(storageKey, sessionId);
        else localStorage.removeItem(storageKey);
      }
      set(sessionId);
    },
    clear() {
      if (typeof localStorage !== 'undefined') localStorage.removeItem(storageKey);
      set(null);
    },
  };
}

export const sessionId = createSessionStore();
export const activityType = writable<ActivityType>(initialActivity as ActivityType);
export const testDuration = writable<30 | 60 | 120>(savedDuration === 60 || savedDuration === 120 ? savedDuration : 30);
export const cameraStream = writable<MediaStream | null>(null);
export const cameraMeta = writable<CameraMeta>({ label: 'Browser camera', mirrored: false, facingMode: '', fps: null });
export const cameraAssignments = writable<Record<CameraView, SavedCameraAssignment>>(savedAssignments());
export const captureViews = writable<Partial<Record<CameraView, CaptureView>>>({});

cameraAssignments.subscribe((value) => {
  if (typeof localStorage !== 'undefined') localStorage.setItem(cameraAssignmentKey, JSON.stringify(value));
});

export function setCaptureViews(next: Partial<Record<CameraView, CaptureView>>) {
  captureViews.set(next);
  const primary = cameraViews.map((view) => next[view]).find(Boolean);
  cameraStream.set(primary?.stream ?? null);
  if (primary) cameraMeta.set({ label: primary.label, mirrored: primary.mirrored, facingMode: '', fps: primary.fps });
}

export function stopCaptureViews() {
  let active: Partial<Record<CameraView, CaptureView>> = {};
  const unsubscribe = captureViews.subscribe((value) => { active = value; });
  unsubscribe();
  Object.values(active).forEach((capture) => capture?.stream.getTracks().forEach((track) => track.stop()));
  setCaptureViews({});
}

activityType.subscribe((value) => {
  if (typeof localStorage !== 'undefined') localStorage.setItem(activityStorageKey, value);
});

testDuration.subscribe((value) => {
  if (typeof localStorage !== 'undefined') localStorage.setItem(durationStorageKey, String(value));
});
