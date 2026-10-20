export type PageId = 'dashboard' | 'studio' | 'report' | 'history' | 'coach';

export interface Session {
  file: string;
  name: string;
  activity: string;
  date: string | null;
  frames: number;
  landmarks: number;
  sample_span_ms: number;
  status: 'saved' | 'empty' | 'unreadable';
  size: number;
}

export interface NavigationItem {
  id: PageId;
  label: string;
  description: string;
}
