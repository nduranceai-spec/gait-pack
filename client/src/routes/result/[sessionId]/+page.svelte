<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { gsap } from 'gsap';
  import AthleteStatueScene from '../../../components/AthleteStatueScene.svelte';
  import Tabs, { type TabItem } from '../../../components/Tabs.svelte';
  import { deleteSession, getGaitResult, getSessionHistory, type GaitResult, type LandmarkFrame, type MetricValue, type SessionHistoryItem, type TimeSeriesPoint } from '../../../lib/api';

  let { sessionId, onRetake = () => {}, onExit = () => {} }: { sessionId: string; onRetake?: () => void; onExit?: () => void } = $props();
  const reportTabs: TabItem[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'replay', label: 'Skeleton replay' },
    { id: 'charts', label: 'Charts' },
    { id: 'quality', label: 'Quality & details' },
  ];
  const overviewMetrics = [
    { key: 'cadence', label: 'Cadence', precision: 0 },
    { key: 'steps', label: 'Steps', precision: 0 },
    { key: 'stepTimeSymmetry', label: 'Step symmetry', precision: 1 },
    { key: 'speed', label: 'Speed', precision: 2 },
  ] as const;
  const connections = [[11,13],[13,15],[12,14],[14,16],[11,12],[11,23],[12,24],[23,24],[23,25],[25,27],[24,26],[26,28],[27,29],[29,31],[28,30],[30,32]];

  let currentSessionId = $state('');
  let activeTab = $state('overview');
  let result = $state<GaitResult | null>(null);
  let loading = $state(true);
  let deleting = $state(false);
  let error = $state('');
  let history = $state<SessionHistoryItem[]>([]);
  let historyOpen = $state(false);
  let displayed = $state<Record<string, number>>({});
  let replayCanvas = $state<HTMLCanvasElement>();
  let replayIndex = $state(0);
  let playing = $state(false);
  let playbackSpeed = $state(1);
  let playbackTimer: ReturnType<typeof setInterval> | undefined;
  let pollTimer: ReturnType<typeof setTimeout> | undefined;
  let selectedView = $state<'all' | 'left' | 'back' | 'right'>('all');

  function metric(key: keyof GaitResult['metrics']): MetricValue | null { return result?.metrics[key] ?? null; }
  function formatMetric(value: MetricValue, precision = 1) { return value.value === null ? 'Unavailable' : `${(displayedKey(value) ?? value.value).toFixed(precision)} ${value.unit}`; }
  function displayedKey(value: MetricValue): number | undefined {
    if (!result) return undefined;
    const entry = Object.entries(result.metrics).find(([, candidate]) => candidate === value);
    return entry ? displayed[entry[0]] : undefined;
  }
  function qualityLabel() {
    const score = result?.quality.score ?? 0;
    return score >= 85 ? 'Strong capture' : score >= 65 ? 'Usable capture' : 'Limited capture';
  }
  function dateLabel(value?: string | null) {
    if (!value || Number.isNaN(Date.parse(value))) return 'Date unavailable';
    return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
  }

  function insights(): string[] {
    if (!result) return [];
    const messages: string[] = [];
    const symmetry = result.metrics.stepTimeSymmetry;
    const cadence = result.metrics.cadence;
    const lean = result.metrics.trunkLean;
    if (symmetry.available && symmetry.value !== null) messages.push(symmetry.value >= 95 ? 'Left and right step timing was closely matched during this capture.' : 'A measurable left–right step-time difference appeared in this capture. Repeat the test before drawing a conclusion.');
    if (cadence.available && cadence.value !== null) messages.push(`GAIT detected ${result.metrics.steps.value ?? 'multiple'} foot contacts at ${Math.round(cadence.value)} steps per minute.`);
    if (lean.available && lean.value !== null) messages.push(`Mean absolute trunk lean was ${lean.value.toFixed(1)}°, based only on frames with visible shoulders and hips.`);
    if (!messages.length) messages.push('This capture does not contain enough reliable timing data for a movement insight. Review Quality & details before retesting.');
    return messages;
  }

  async function loadResult(id = currentSessionId) {
    if (pollTimer) clearTimeout(pollTimer);
    stopPlayback();
    loading = true; error = ''; currentSessionId = id; replayIndex = 0; displayed = {};
    try {
      result = await getGaitResult(id);
      history = (await getSessionHistory().catch(() => [])).filter((item) => item.sessionId);
      await tick();
      gsap.fromTo('.result-reveal', { y: 26, opacity: 0 }, { y: 0, opacity: 1, duration: .62, stagger: .065, ease: 'power4.out' });
      Object.entries(result.metrics).forEach(([key, value]) => {
        if (!value.available || value.value === null) return;
        const counter = { value: 0 };
        gsap.to(counter, { value: value.value, duration: .9, ease: 'power3.out', onUpdate: () => { displayed = { ...displayed, [key]: counter.value }; } });
      });
      if (result.state === 'processing' || result.state === 'recording') pollTimer = setTimeout(() => void loadResult(id), 850);
    } catch (failure) { error = failure instanceof Error ? failure.message : 'We could not load this GAIT report.'; }
    finally { loading = false; if (activeTab === 'replay') requestAnimationFrame(drawReplay); }
  }

  function selectTab(id: string) {
    activeTab = id;
    stopPlayback();
    tick().then(() => {
      gsap.fromTo('.tab-panel', { y: 15, opacity: 0 }, { y: 0, opacity: 1, duration: .4, ease: 'power3.out' });
      if (id === 'replay') drawReplay();
    });
  }

  function timeline(): LandmarkFrame[] {
    if (!result) return [];
    return selectedView === 'all' ? result.landmarkTimeline : result.landmarksByView?.[selectedView] ?? [];
  }
  function currentFrame(): LandmarkFrame | null { return timeline()[replayIndex] ?? null; }

  function drawReplay() {
    if (!replayCanvas) return;
    const context = replayCanvas.getContext('2d');
    if (!context) return;
    const width = replayCanvas.width = 900;
    const height = replayCanvas.height = 520;
    context.fillStyle = '#07171c'; context.fillRect(0, 0, width, height);
    context.strokeStyle = '#17343c'; context.lineWidth = 1;
    for (let x = 0; x <= width; x += 90) { context.beginPath(); context.moveTo(x, 0); context.lineTo(x, height); context.stroke(); }
    for (let y = 0; y <= height; y += 65) { context.beginPath(); context.moveTo(0, y); context.lineTo(width, y); context.stroke(); }
    const selectedTimeline = timeline();
    const frame = selectedTimeline[replayIndex];
    if (!frame?.keypoints.length) {
      context.fillStyle = '#a9b9bc'; context.font = '700 16px Manrope, sans-serif'; context.textAlign = 'center'; context.fillText('Body was not detected in this frame', width / 2, height / 2);
      return;
    }
    const points = frame.keypoints;
    const start = Math.max(0, replayIndex - 35);
    selectedTimeline.slice(start, replayIndex + 1).forEach((trailFrame, index) => {
      const alpha = (index + 1) / Math.max(1, replayIndex - start + 1) * .55;
      const left = trailFrame.keypoints[31] ?? trailFrame.keypoints[27];
      const right = trailFrame.keypoints[32] ?? trailFrame.keypoints[28];
      if (left?.visibility >= .4) { context.globalAlpha = alpha; context.fillStyle = '#00e5ff'; context.beginPath(); context.ellipse(left.x * width, left.y * height, 13, 5, 0, 0, Math.PI * 2); context.fill(); }
      if (right?.visibility >= .4) { context.globalAlpha = alpha; context.fillStyle = '#ff7a00'; context.beginPath(); context.ellipse(right.x * width, right.y * height, 13, 5, 0, 0, Math.PI * 2); context.fill(); }
    });
    context.globalAlpha = 1; context.strokeStyle = '#00e5ff'; context.fillStyle = '#00e5ff'; context.lineWidth = 4; context.lineCap = 'round';
    connections.forEach(([from, to]) => {
      const a = points[from], b = points[to];
      if (!a || !b || a.visibility < .4 || b.visibility < .4) return;
      context.beginPath(); context.moveTo(a.x * width, a.y * height); context.lineTo(b.x * width, b.y * height); context.stroke();
    });
    points.forEach((point) => { if (point.visibility >= .4) { context.beginPath(); context.arc(point.x * width, point.y * height, 5, 0, Math.PI * 2); context.fill(); } });
  }

  function setReplayIndex(value: number) {
    replayIndex = Math.max(0, Math.min(Math.max(0, timeline().length - 1), value));
    drawReplay();
  }

  function togglePlayback() {
    if (playing) { stopPlayback(); return; }
    if (!timeline().length) return;
    playing = true;
    playbackTimer = setInterval(() => {
      if (!result) return;
      if (replayIndex >= timeline().length - 1) replayIndex = 0;
      else replayIndex += 1;
      drawReplay();
    }, 100 / playbackSpeed);
  }

  function stopPlayback() { playing = false; if (playbackTimer) clearInterval(playbackTimer); playbackTimer = undefined; }
  function setSpeed(speed: number) { playbackSpeed = speed; if (playing) { stopPlayback(); togglePlayback(); } }

  function pathFor(key: keyof TimeSeriesPoint, maxValue = 180): string {
    if (!result?.timeSeries.length) return '';
    const duration = Math.max(.1, result.durationSec);
    return result.timeSeries.flatMap((point) => {
      const value = point[key];
      if (typeof value !== 'number') return [];
      return [`${point.t / duration * 760},${190 - value / maxValue * 170}`];
    }).map((point, index) => `${index ? 'L' : 'M'}${point}`).join(' ');
  }

  function swayPath(): string {
    const points = result?.timeSeries.filter((point) => typeof point.swayX === 'number' && typeof point.swayY === 'number') ?? [];
    if (!points.length) return '';
    const xs = points.map((point) => point.swayX as number), ys = points.map((point) => point.swayY as number);
    const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
    return points.map((point, index) => {
      const x = 40 + ((point.swayX as number) - minX) / Math.max(.001, maxX - minX) * 680;
      const y = 20 + ((point.swayY as number) - minY) / Math.max(.001, maxY - minY) * 170;
      return `${index ? 'L' : 'M'}${x},${y}`;
    }).join(' ');
  }

  async function removeSession() {
    if (!confirm('Delete this GAIT session and its landmark data? This cannot be undone.')) return;
    deleting = true; error = '';
    try { await deleteSession(currentSessionId); onExit(); }
    catch (failure) { error = failure instanceof Error ? failure.message : 'The session could not be deleted.'; deleting = false; }
  }

  function setView(view: 'all' | 'left' | 'back' | 'right') { selectedView = view; replayIndex = 0; drawReplay(); }
  onMount(() => { currentSessionId = sessionId; void loadResult(sessionId); return () => { stopPlayback(); if (pollTimer) clearTimeout(pollTimer); }; });
</script>

<svelte:head><title>GAIT — Movement report</title></svelte:head>

<main class="result-shell">
  <header class="result-header result-reveal">
    <button class="wordmark" onclick={onExit}>GAIT<span>®</span></button>
    <p>Final result / <b>{result?.activity ?? 'Loading'}</b></p>
  </header>

  {#if error}<div class="error" role="alert">{error}<button onclick={() => loadResult()}>Try again</button></div>{/if}

  <section class="report-hero result-reveal" aria-labelledby="report-title">
    <div><p class="eyebrow">CAPTURE COMPLETE</p><h1 id="report-title">Movement<br /><em>profile.</em></h1><p class="profile-name">{result?.person?.name ?? 'Participant'} <span>· {result?.activity ?? 'Loading'}</span></p></div>
    <div class="session-meta"><span class:strong={(result?.quality.score ?? 0) >= 85}>{qualityLabel()} · {result?.quality.score ?? 0}/100</span><p>{dateLabel(result?.timestamp)}<br />{result?.durationSec.toFixed(0) ?? '0'} seconds<br />Saved locally</p></div>
  </section>

  {#if loading || result?.state === 'processing'}<div class="loading">Analyzing your movement… <small>Only landmarks are stored; raw camera images are never saved.</small></div>
  {:else if result}
    {#if activeTab === 'overview'}
      <div class="tab-panel overview" role="tabpanel" aria-label="Overview" tabindex="0">
        <div class="performance-board">
          <article class="avatar-card"><p class="eyebrow">MOVEMENT AVATAR</p><div class="statue"><AthleteStatueScene statue={true} /></div><small>Drag to rotate · movement reference</small></article>
          <article class="score-card"><p class="eyebrow">PERFORMANCE SCORE</p><strong>{result.quality.score}<span>/100</span></strong><i style={`--score:${result.quality.score}`}></i><small>{qualityLabel()}</small></article>
          <article class="bio-card"><p class="eyebrow">PARTICIPANT</p><strong>{result.person?.name ?? '—'}</strong><dl><div><dt>Age</dt><dd>{result.person?.age ?? '—'}</dd></div><div><dt>Height</dt><dd>{result.person?.height ? `${result.person.height} cm` : '—'}</dd></div><div><dt>Weight</dt><dd>{result.person?.weight ? `${result.person.weight} kg` : '—'}</dd></div></dl></article>
        </div>
        <div class="metric-grid">
          {#each overviewMetrics as item, index}
            {@const value = metric(item.key)}
            <article class:unavailable={!value?.available} class:cyan={index === 2} class:dark={index === 3} class="metric-card result-reveal">
              <p>{item.label}</p>
              {#if value?.available && value.value !== null}<strong>{formatMetric(value, item.precision)}</strong><small>{Math.round(value.confidence * 100)}% signal confidence</small>
              {:else}<strong class="unavailable-label">Unavailable</strong><small>{value?.reason ?? 'No reliable value was produced.'}</small>{/if}
            </article>
          {/each}
        </div>
        <div class="overview-lower">
          <article class="quality-card"><p class="eyebrow">CAPTURE QUALITY</p><strong>{result.quality.score}<span>/100</span></strong><div><i style={`transform:scaleX(${result.quality.score / 100})`}></i></div><small>{result.quality.notes[0]}</small></article>
          <article class="insights"><p class="eyebrow">WHAT THE DATA SHOWS</p>{#each insights() as insight}<p>{insight}</p>{/each}</article>
        </div>
      </div>
    {:else if activeTab === 'replay'}
      <div class="tab-panel replay" role="tabpanel" aria-label="Skeleton replay" tabindex="0">
        <div class="replay-stage"><canvas bind:this={replayCanvas}></canvas><span>LANDMARKS ONLY · NO RAW VIDEO STORED</span></div>
        <div class="replay-controls"><button onclick={togglePlayback}>{playing ? 'Pause' : 'Play'} {playing ? 'Ⅱ' : '▶'}</button><input aria-label="Replay position" type="range" min="0" max={Math.max(0, timeline().length - 1)} value={replayIndex} oninput={(event) => setReplayIndex(Number(event.currentTarget.value))} /><time>{currentFrame()?.t.toFixed(1) ?? '0.0'}s / {result.durationSec.toFixed(1)}s</time><div>{#each [0.25, 0.5, 1] as speed}<button class:active={playbackSpeed === speed} onclick={() => setSpeed(speed)}>{speed}×</button>{/each}</div></div>
      </div>
    {:else if activeTab === 'charts'}
      <div class="tab-panel charts" role="tabpanel" aria-label="Charts" tabindex="0">
        <article class="chart-card"><header><div><p class="eyebrow">JOINT MOTION</p><h2>Knee angle, left vs right</h2></div><div class="legend"><span class="left">Left</span><span class="right">Right</span></div></header><svg viewBox="0 0 760 200" preserveAspectRatio="none" aria-label="Knee-angle chart"><path class="grid" d="M0 20H760M0 62H760M0 105H760M0 147H760M0 190H760"/><path class="left-line" d={pathFor('leftKnee')}/><path class="right-line" d={pathFor('rightKnee')}/><line class="cursor" x1={(currentFrame()?.t ?? 0) / Math.max(.1,result.durationSec) * 760} x2={(currentFrame()?.t ?? 0) / Math.max(.1,result.durationSec) * 760} y1="0" y2="200"/></svg></article>
        <article class="chart-card"><header><div><p class="eyebrow">HIP MOTION</p><h2>Hip angle, left vs right</h2></div><div class="legend"><span class="left">Left</span><span class="right">Right</span></div></header><svg viewBox="0 0 760 200" preserveAspectRatio="none" aria-label="Hip-angle chart"><path class="grid" d="M0 20H760M0 62H760M0 105H760M0 147H760M0 190H760"/><path class="left-line" d={pathFor('leftHip')}/><path class="right-line" d={pathFor('rightHip')}/><line class="cursor" x1={(currentFrame()?.t ?? 0) / Math.max(.1,result.durationSec) * 760} x2={(currentFrame()?.t ?? 0) / Math.max(.1,result.durationSec) * 760} y1="0" y2="200"/></svg></article>
        {#if result.activity === 'Balance'}<article class="chart-card sway"><header><div><p class="eyebrow">BALANCE</p><h2>Normalized sway path</h2></div><small>Hip-centre motion, not centimetres</small></header><svg viewBox="0 0 760 220" aria-label="Sway path"><path class="grid" d="M40 20H720M40 105H720M40 190H720M40 20V190M380 20V190M720 20V190"/><path class="sway-line" d={swayPath()}/></svg></article>{/if}
        <div class="chart-scrubber"><span>Charts and replay position</span><input aria-label="Chart position" type="range" min="0" max={Math.max(0, result.landmarkTimeline.length - 1)} value={replayIndex} oninput={(event) => setReplayIndex(Number(event.currentTarget.value))} /></div>
      </div>
    {:else}
      <div class="tab-panel details" role="tabpanel" aria-label="Quality and details" tabindex="0">
        <div class="detail-grid"><article><p class="eyebrow">FRAMES</p><strong>{result.detectedFrames}<span> / {result.frameCount}</span></strong><small>frames contained a detected body</small></article><article><p class="eyebrow">FULL BODY</p><strong>{Math.round(result.quality.fullBodyRatio * 100)}<span>%</span></strong><small>frames with shoulders, hips, knees and ankles</small></article><article><p class="eyebrow">FEET VISIBLE</p><strong>{Math.round(result.quality.feetVisibleRatio * 100)}<span>%</span></strong><small>frames with ankles, heels and foot tips</small></article><article><p class="eyebrow">CAMERA</p><strong class="camera-name">{result.camera.name}</strong><small>{result.camera.fps ? `${result.camera.fps} FPS reported` : 'FPS unavailable'}</small></article></div>
        <div class="quality-list"><div><p class="eyebrow">QUALITY NOTES</p>{#each result.quality.notes as note}<p>→ {note}</p>{/each}{#if result.quality.missingSegments.length}<p>→ Missing-body segments: {result.quality.missingSegments.map((segment) => `${segment.start}s–${segment.end}s`).join(', ')}</p>{/if}</div><div><p class="eyebrow">UNAVAILABLE METRICS</p>{#each Object.entries(result.metrics).filter(([, value]) => !value.available) as [key, value]}<p><b>{key.replace(/([A-Z])/g, ' $1')}</b> — {value.reason}</p>{/each}</div></div>
        {#if result.views?.length}<div class="view-details">{#each result.views as view}<article><b>{view.view.toUpperCase()}</b><span>{view.cameraLabel}</span><small>{view.received} received · {view.detected} body detected · {Math.round(view.detectionRate * 100)}%</small><small>{view.width ?? '—'}×{view.height ?? '—'} · {view.fps ?? '—'} FPS · {view.rotation}°</small>{#if view.gaps.length}<small>Gaps: {view.gaps.map((gap) => `${gap.start}s–${gap.end}s`).join(', ')}</small>{/if}</article>{/each}</div>{/if}
      </div>
    {/if}

    <aside class="privacy-note result-reveal"><span>⌁</span><div><strong>Saved on this laptop</strong><p>Participant data, pose analysis, and the recorded left, back, and right camera views are stored locally in the session folder.</p></div></aside>
  {/if}

  <footer class="report-actions result-reveal"><button class="back" onclick={onExit}>Exit</button><button class="retake" onclick={onRetake}>RUN ANOTHER TEST <span>→</span></button></footer>

  {#if historyOpen}<aside class="history-drawer" aria-label="Previous GAIT sessions"><header><div><p class="eyebrow">HISTORY</p><h2>Previous tests</h2></div><button onclick={() => historyOpen = false}>Close</button></header>{#if history.length}{#each history as item}<button class:active={item.sessionId === currentSessionId} class="history-item" onclick={() => item.sessionId && loadResult(item.sessionId)}><span><b>{item.activity}</b><small>{dateLabel(item.date)}</small></span><strong>{item.frames} frames</strong></button>{/each}{:else}<p>No previous browser sessions are available.</p>{/if}</aside>{/if}
</main>

<style>
  .result-shell{min-height:100svh;padding:0 clamp(18px,3vw,42px) 38px;background:var(--paper);color:var(--ink)}button{font:inherit}.result-header{height:86px;display:grid;grid-template-columns:1fr auto 1fr;align-items:center}.wordmark,.history-button,.report-actions button,.error button{border:0;background:none;color:inherit;font-weight:800}.wordmark{justify-self:start;font-size:21px;letter-spacing:-.1em}.wordmark span,.retake span{color:var(--cyan);font-size:10px;vertical-align:top}.result-header p{margin:0;color:var(--muted);font-size:12px}.result-header p b{color:var(--ink)}.history-button{justify-self:end}.history-button span{display:inline-grid;place-items:center;min-width:22px;height:22px;margin-left:7px;background:var(--cyan);font-size:10px}.report-hero{max-width:1240px;margin:clamp(45px,7vw,96px) auto 0;display:grid;grid-template-columns:1.25fr .75fr;gap:50px;align-items:end}.eyebrow{margin:0 0 13px;color:var(--muted);font-size:10px;font-weight:800;letter-spacing:.09em}.report-hero h1{margin:0;font-size:clamp(62px,8.8vw,128px);line-height:.8;letter-spacing:-.11em}.report-hero h1 em{color:var(--cyan);font-style:normal}.session-meta{justify-self:end;text-align:right}.session-meta>span{display:inline-block;padding:8px 10px;background:#ffdfb3;color:#6d4510;font-size:10px;font-weight:800}.session-meta>span.strong{background:#cef5e6;color:#145f48}.session-meta p{margin:15px 0 0;color:var(--muted);font-size:13px;line-height:1.65}.tab-row{max-width:1240px;margin:55px auto 0;border-bottom:1px solid #aebabb;padding-bottom:10px}.loading,.error{max-width:1240px;margin:55px auto;padding:18px;background:#e7eeee}.error{display:flex;justify-content:space-between;background:#ffe9e4;color:#852814;font-size:13px;font-weight:700}.error button{text-decoration:underline}.tab-panel{max-width:1240px;margin:36px auto 0}.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.metric-card{min-height:225px;padding:21px;background:#dff8ff;display:flex;flex-direction:column;justify-content:space-between}.metric-card:nth-child(2){background:#e7eeee}.metric-card.cyan{background:var(--cyan)}.metric-card.dark{background:var(--ink);color:#f8f8f6}.metric-card.unavailable{background:#eaeeee!important;color:#708085!important}.metric-card p{margin:0;font-size:12px;font-weight:800}.metric-card strong{font-size:clamp(34px,4vw,62px);line-height:.86;letter-spacing:-.09em}.metric-card .unavailable-label{font-size:clamp(23px,2.5vw,38px);letter-spacing:-.06em}.metric-card small{font-size:10px;line-height:1.45;opacity:.68}.overview-lower{display:grid;grid-template-columns:.72fr 1.28fr;gap:8px;margin-top:8px}.quality-card,.insights{padding:24px;background:var(--ink);color:#f8f8f6}.quality-card strong{font-size:clamp(54px,7vw,90px);letter-spacing:-.1em}.quality-card strong span{font-size:.3em;color:#afbec1}.quality-card>div{height:5px;margin:24px 0 14px;background:#ffffff24}.quality-card i{display:block;width:100%;height:100%;background:var(--cyan);transform-origin:left}.quality-card small{color:#afbec1}.insights{background:#e7eeee;color:var(--ink)}.insights>p:not(.eyebrow){max-width:720px;margin:16px 0 0;font-size:clamp(17px,2vw,25px);line-height:1.25;letter-spacing:-.04em}.replay-stage{position:relative;background:var(--ink);aspect-ratio:16/9;max-height:650px}.replay-stage canvas{display:block;width:100%;height:100%}.replay-stage>span{position:absolute;top:16px;left:16px;color:#9db0b4;font-size:9px;font-weight:800;letter-spacing:.08em}.replay-controls{display:grid;grid-template-columns:auto 1fr auto auto;align-items:center;gap:16px;padding:14px;background:#e7eeee}.replay-controls button{border:0;background:var(--ink);color:#fff;padding:10px 13px;font-weight:800}.replay-controls>div{display:flex;gap:4px}.replay-controls>div button{background:transparent;color:var(--ink);border:1px solid #9dacad}.replay-controls>div button.active{background:var(--cyan);border-color:var(--cyan)}input[type=range]{width:100%;accent-color:var(--cyan)}.charts{display:grid;grid-template-columns:1fr 1fr;gap:8px}.chart-card{padding:22px;background:#e7eeee}.chart-card header{display:flex;justify-content:space-between;gap:20px;align-items:start}.chart-card h2{margin:0;font-size:22px;letter-spacing:-.06em}.chart-card svg{display:block;width:100%;height:240px;margin-top:20px;overflow:visible}.chart-card path{fill:none;vector-effect:non-scaling-stroke}.grid{stroke:#aab8ba;stroke-width:1}.left-line{stroke:#00a9d1;stroke-width:3}.right-line{stroke:#ff7a00;stroke-width:3}.cursor{stroke:#07171c;stroke-width:1;stroke-dasharray:4 4}.legend{display:flex;gap:13px;font-size:10px;font-weight:800}.legend span:before{content:"";display:inline-block;width:8px;height:8px;margin-right:5px;background:#00a9d1}.legend .right:before{background:#ff7a00}.sway{grid-column:1/-1}.sway-line{stroke:var(--cyan);stroke-width:3}.chart-scrubber{grid-column:1/-1;display:grid;grid-template-columns:auto 1fr;gap:20px;align-items:center;padding:14px 20px;background:var(--ink);color:#fff;font-size:11px;font-weight:800}.detail-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.detail-grid article{min-height:190px;padding:21px;background:#e7eeee;display:flex;flex-direction:column;justify-content:space-between}.detail-grid article:nth-child(2){background:#dff8ff}.detail-grid article:nth-child(3){background:var(--cyan)}.detail-grid article:nth-child(4){background:var(--ink);color:#fff}.detail-grid strong{font-size:clamp(42px,5vw,70px);line-height:.85;letter-spacing:-.1em}.detail-grid strong span{font-size:.35em}.detail-grid .camera-name{font-size:clamp(20px,2.3vw,34px);letter-spacing:-.06em}.detail-grid small{font-size:10px;opacity:.65}.quality-list{display:grid;grid-template-columns:.8fr 1.2fr;gap:8px;margin-top:8px}.quality-list>div{padding:24px;background:#e7eeee}.quality-list>div+div{background:#dff8ff}.quality-list p:not(.eyebrow){margin:10px 0;color:#34474c;font-size:12px;line-height:1.5}.privacy-note{max-width:1240px;margin:22px auto 0;padding:18px 20px;border:1px solid #aebbbc;display:flex;gap:14px;align-items:start}.privacy-note>span{font-size:25px;color:#0089aa}.privacy-note strong{font-size:13px}.privacy-note p{margin:5px 0 0;color:var(--muted);font-size:11px;line-height:1.5}.report-actions{max-width:1240px;margin:24px auto 0;display:flex;justify-content:space-between;gap:15px}.report-actions>div{display:flex;gap:8px}.report-actions button{padding:14px 17px}.back,.delete{border:1px solid #9eadaf!important}.delete{color:#8a321f!important}.retake{background:var(--ink)!important;color:#fff!important}.retake span{margin-left:14px;font-size:17px}.history-drawer{position:fixed;z-index:20;top:0;right:0;width:min(420px,100vw);height:100dvh;padding:28px;background:var(--paper);box-shadow:-30px 0 80px #07171c26;overflow:auto}.history-drawer header{display:flex;justify-content:space-between;align-items:start;margin-bottom:34px}.history-drawer h2{margin:0;font-size:36px;letter-spacing:-.08em}.history-drawer header button{border:0;background:none;font-weight:800}.history-item{width:100%;display:flex;justify-content:space-between;gap:20px;padding:17px 0;border:0;border-bottom:1px solid #aab7b9;background:none;text-align:left}.history-item.active{color:#0085a5}.history-item span{display:grid}.history-item small{margin-top:5px;color:var(--muted)}
  @media(max-width:800px){.result-header{grid-template-columns:1fr auto}.result-header p{display:none}.report-hero{grid-template-columns:1fr;gap:28px;margin-top:48px}.session-meta{justify-self:start;text-align:left}.tab-row{margin-top:38px;overflow:hidden}.metric-grid,.detail-grid{grid-template-columns:1fr 1fr}.metric-card{min-height:180px}.overview-lower,.quality-list,.charts{grid-template-columns:1fr}.sway,.chart-scrubber{grid-column:auto}.report-actions{align-items:stretch;flex-direction:column}.report-actions>div{display:grid;grid-template-columns:1fr 1fr}.replay-controls{grid-template-columns:auto 1fr}.replay-controls time{grid-column:1}.replay-controls>div{grid-column:2}.chart-card svg{height:190px}}
  @media(max-width:480px){.metric-grid,.detail-grid{grid-template-columns:1fr}.metric-card,.detail-grid article{min-height:155px}.replay-controls{gap:9px;padding:10px}.report-hero h1{font-size:clamp(58px,18vw,88px)}}
  .view-filter{max-width:1240px;margin:12px auto 0;display:flex;gap:6px;align-items:center}.view-filter span{margin-right:4px;color:var(--muted);font-size:9px;font-weight:800;letter-spacing:.1em}.view-filter button{border:1px solid #aebabc;background:transparent;padding:7px 10px;color:var(--ink);font-size:10px;font-weight:800;text-transform:uppercase}.view-filter button.active{border-color:var(--ink);background:var(--ink);color:var(--paper)}.view-details{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px;margin-top:8px}.view-details article{display:grid;gap:6px;padding:16px;background:#dff8ff}.view-details b{font-size:12px;letter-spacing:.08em}.view-details span{font-size:13px;font-weight:800}.view-details small{color:var(--muted);font-size:10px;line-height:1.45}
  @media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}.result-reveal{transform:none!important;opacity:1!important}}
  .profile-name{margin:20px 0 0;font-size:18px;font-weight:800}.profile-name span{color:var(--muted);font-weight:600}.performance-board{display:grid;grid-template-columns:1.15fr .65fr .8fr;gap:8px;margin-bottom:8px}.avatar-card,.score-card,.bio-card{min-height:330px;padding:20px;background:#e7eeee}.avatar-card{position:relative;overflow:hidden}.statue{height:255px;margin:-8px auto 0}.avatar-card small{display:block;text-align:center;color:var(--muted);font-size:9px}.score-card{background:#dff8ff;display:flex;flex-direction:column}.score-card strong{font-size:clamp(72px,9vw,132px);line-height:.8;letter-spacing:-.12em}.score-card strong span{font-size:.22em}.score-card i{width:100%;height:8px;margin:auto 0 15px;background:linear-gradient(90deg,var(--cyan) calc(var(--score) * 1%),#aebbbc 0)}.score-card small{font-size:11px;font-weight:800}.bio-card{background:var(--ink);color:#f8f8f6}.bio-card .eyebrow{color:#a9b9bc}.bio-card>strong{font-size:clamp(28px,3vw,44px);letter-spacing:-.07em}.bio-card dl{margin:auto 0 0}.bio-card dl div{display:flex;justify-content:space-between;padding:11px 0;border-top:1px solid #ffffff26}.bio-card dt{color:#a9b9bc;font-size:10px}.bio-card dd{margin:0;font-size:13px;font-weight:800}@media(max-width:800px){.performance-board{grid-template-columns:1fr 1fr}.avatar-card{grid-column:1/-1}}@media(max-width:480px){.performance-board{grid-template-columns:1fr}.avatar-card{grid-column:auto}}
</style>
