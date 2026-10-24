<script lang="ts">
  import { onMount } from 'svelte';
  import { ArrowUpRight, Camera, Check, CircleStop, Play, ScanLine, Usb } from '@lucide/svelte';
  import GlassCard from '../components/GlassCard.svelte';
  import StatusPill from '../components/StatusPill.svelte';
  import HelpAccordion from '../components/HelpAccordion.svelte';
  let { autoStart = false, onSaved, onReport }: { autoStart?: boolean; onSaved: () => void; onReport: (file: string) => void } = $props();
  interface CameraStatus {
    state: string;
    error: string;
    camera: string;
    pose_fps: number;
    hand_fps: number;
    body_detected: boolean;
    recording: string;
    frames: number;
    remaining: number;
    file: string | null;
  }
  let status = $state<CameraStatus | null>(null);
  let error = $state('');
  let connectionError = $state('');
  let busy = $state(false);
  let preview = $state('');
  let disposed = false;
  let notifiedFile = '';
  let online = $derived(status?.state === 'running');
  let recording = $derived(online && status?.recording === 'RECORDING');
  let transitioning = $derived(status?.state === 'starting' || status?.state === 'stopping');
  let seconds = $derived(recording ? status?.remaining ?? 60 : 60);

  function acceptStatus(result: CameraStatus) {
    connectionError = '';
    status = result;
    if (result.recording === 'STOPPED' && result.file && result.file !== notifiedFile) {
      notifiedFile = result.file;
      onSaved();
    }
  }

  async function command(action: string) {
    busy = true;
    error = '';
    try {
      const response = await fetch(`/api/${action}`, {
        method: 'POST', headers: { 'X-Gait-Control': '1' }, signal: AbortSignal.timeout(10000),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Camera request failed.');
      if (!disposed) acceptStatus(result);
    } catch (failure) {
      if (!disposed) error = failure instanceof Error ? failure.message : 'Backend unavailable.';
    } finally {
      busy = false;
    }
  }

  onMount(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function refresh() {
      try {
        const response = await fetch('/api/status', { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(5000)]) });
        if (!response.ok) throw new Error('Backend unavailable.');
        const result: CameraStatus = await response.json();
        if (disposed) return;
        if (!busy) acceptStatus(result);
        if (result.state === 'running') {
          const frame = await fetch(`/api/frame?t=${Date.now()}`, { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(5000)]) });
          if (frame.ok) {
            const blob = await frame.blob();
            if (disposed) return;
            const oldPreview = preview;
            preview = URL.createObjectURL(blob);
            if (oldPreview) URL.revokeObjectURL(oldPreview);
          }
        } else if (preview) {
          URL.revokeObjectURL(preview);
          preview = '';
        }
      } catch {
        if (!disposed) {
          status = null;
          connectionError = 'Cannot reach the backend. Start python scripts/run_web.py and check its terminal.';
          if (preview) URL.revokeObjectURL(preview);
          preview = '';
        }
      } finally {
        if (!disposed) timer = setTimeout(refresh, status?.state === 'running' ? 80 : 800);
      }
    }
    if (autoStart) void command('test/start');
    void refresh();
    return () => {
      disposed = true;
      controller.abort();
      clearTimeout(timer);
      if (preview) URL.revokeObjectURL(preview);
      void fetch('/api/camera/stop', { method: 'POST', headers: { 'X-Gait-Control': '1' }, keepalive: true }).catch(() => {});
    };
  });
</script>

<div class="page-stack">
  <div class="studio-heading"><div><p class="eyebrow">A little preparation. A better capture.</p><h2>Find your frame.</h2></div><span class="workspace-badge"><Usb size={15} /> USB camera · 60-second test</span></div>
  <ol class="setup-steps" aria-label="Capture readiness">
    <li class:step-ready={online && Boolean(preview)}><span class="readiness-number">{#if online && preview}<Check size={17} />{:else}01{/if}</span><div><strong>Connect camera</strong><small>{online && preview ? 'Preview is available' : 'Open your USB preview'}</small></div></li>
    <li class:step-ready={online && status?.body_detected}><span class="readiness-number">{#if online && status?.body_detected}<Check size={17} />{:else}02{/if}</span><div><strong>Check your position</strong><small>{online && status?.body_detected ? 'Body detected · check feet in frame' : 'Keep your full body in view'}</small></div></li>
    <li class:step-ready={recording}><span class="readiness-number">{#if recording}<Check size={17} />{:else}03{/if}</span><div><strong>Move naturally</strong><small>{recording ? 'Your recording is in progress' : 'Start when you feel ready'}</small></div></li>
  </ol>
  <div class="capture-layout">
    <GlassCard class="capture-viewport" elevated>
      <div class="preview-topline"><StatusPill label={recording ? 'Recording' : online ? 'Live preview' : status?.state === 'starting' ? 'Connecting' : 'Camera offline'} pulse={recording} /><span>{status?.camera || 'USB / AUTO-DETECT'}</span></div>
      <div class="live-stage">
        {#if preview}<img class="live-camera" src={preview} alt="Live USB camera with body and hand tracking" />
        {:else}<div class="camera-empty-state"><div class="viewfinder-art"><ScanLine size={72} strokeWidth={.8} /></div><p class="eyebrow">Your movement, in focus</p><h3>{status?.state === 'starting' ? 'Preparing your camera…' : 'A clear view starts here.'}</h3><p>{status?.state === 'starting' ? 'Loading the camera and tracking models.' : 'Connect your USB camera. We’ll bring your movement into the frame.'}</p></div>{/if}
        <div class="tracking-annotations"><span><i class:detected={online && status?.body_detected}></i>{online && status?.body_detected ? 'Body detected' : 'Waiting for body'}</span><span>Pose <b>{online ? status?.pose_fps ?? 0 : '—'}</b> FPS</span><span>Hands <b>{online ? status?.hand_fps ?? 0 : '—'}</b> FPS</span></div>
        <div class="floating-capture-dock" aria-label="Camera and recording controls">
          <button class="dock-camera" disabled={busy || transitioning || recording} onclick={() => command('camera/start')}><Camera size={19} /><span>Camera</span></button>
          <span class="dock-divider"></span>
          <button class="primary-button" disabled={busy || recording || transitioning} onclick={() => command('test/start')}><Play size={16} fill="currentColor" /> {recording ? 'Recording…' : 'Start 60s test'}</button>
          <button class="dock-stop" disabled={busy || (!online && !transitioning)} onclick={() => command('camera/stop')}><CircleStop size={20} /><span>Save & stop</span></button>
        </div>
      </div>
      <div class="preview-bottomline"><span>BODY + HAND TRACKING</span><span>Video preview only · CSV recording</span></div>
    </GlassCard>

    <div class="capture-sidebar">
      <GlassCard class="session-progress-card">
        <p class="eyebrow">Your capture</p><h3>{recording ? 'One step at a time.' : status?.recording === 'STOPPED' ? 'Recording saved.' : 'Ready at your pace.'}</h3>
        <div class="capture-timer"><strong>{recording ? String(seconds).padStart(2, '0') : '60'}</strong><span>{recording ? 'seconds remaining' : 'second capture window'}</span></div>
        <progress max="60" value={recording ? 60 - seconds : 0} aria-label="Recording progress"></progress>
        <div class="capture-detail"><span>Recorded pose frames</span><strong>{status?.frames ?? 0}</strong></div>
        <div class="capture-detail"><span>Recording state</span><strong>{status?.recording === 'STOPPED' ? 'Saved' : recording ? 'Recording' : 'Not recording'}</strong></div>
        {#if status?.file && status.recording === 'STOPPED'}<button class="secondary-button review-recording" onclick={() => status?.file && onReport(status.file)}>Review recording <ArrowUpRight size={17} /></button>{/if}
      </GlassCard>
      {#if connectionError || error || status?.error}<div class="inline-notice" role="alert"><strong>Let’s check the connection.</strong><p>{connectionError || error || status?.error}</p><button class="text-button" disabled={busy || transitioning} onclick={() => command('camera/start')}>Retry camera</button></div>{/if}
      <GlassCard class="capture-help"><p class="eyebrow">Small details matter</p><h3>Make space to move.</h3><HelpAccordion items={[
        { question: 'What makes a good frame?', answer: 'Keep your full body and feet visible. Use even lighting and a stable camera. Body detected confirms a pose was found, not that every landmark is reliable.' },
        { question: 'What happens at 60 seconds?', answer: 'The CSV saves automatically and the live preview stays open. Save & stop releases the camera. You can also stop early.' },
        { question: 'What do these live labels mean?', answer: 'Pose and hand FPS are inference rates. They do not measure tracking accuracy. Recorded pose frames counts the unique samples saved to your CSV.' }
      ]} /></GlassCard>
    </div>
  </div>
</div>
