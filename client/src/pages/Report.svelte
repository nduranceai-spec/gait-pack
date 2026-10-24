<script lang="ts">
  import { ArrowDownToLine, ArrowLeft, ArrowRight, Activity, Clock3, ScanLine, FileText } from '@lucide/svelte';
  import GlassCard from '../components/GlassCard.svelte';
  import StatusPill from '../components/StatusPill.svelte';
  import HelpAccordion from '../components/HelpAccordion.svelte';
  import type { Session } from '../lib/types';
  import { sessionDate, sessionDownload, sessionDuration } from '../lib/sessions';
  let { session, loading, error, onHistory, onStart }: {
    session: Session | null; loading: boolean; error: string; onHistory: () => void; onStart: () => void;
  } = $props();
  const tabs = ['Overview', 'Joint angles', 'Symmetry', 'Recording details'];
  let activeTab = $state(0);
  function changeTab(event: KeyboardEvent, index: number) {
    let next = index;
    if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
    else if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = tabs.length - 1;
    else return;
    event.preventDefault();
    activeTab = next;
    document.getElementById(`report-tab-${next}`)?.focus();
  }
</script>

<div class="page-stack">
  <button class="text-button back-link" onclick={onHistory}><ArrowLeft size={16} /> All recordings</button>
  {#if loading && !session}<GlassCard><p role="status">Loading your report…</p></GlassCard>
  {:else if !session}
    <GlassCard class="report-empty"><FileText size={40} strokeWidth={1.2} /><p class="eyebrow">The detail starts with a recording</p><h2>Your next step,<br /><em>in perspective.</em></h2><p>{error || 'Capture a session to explore its recorded frames, timing, and landmark data.'}</p><button class="primary-button" onclick={onStart}>Set up a test <ArrowRight size={18} /></button></GlassCard>
  {:else}
    <div class="page-intro report-intro"><div><StatusPill label={session.status === 'saved' ? 'Saved recording' : session.status === 'empty' ? 'No pose data' : 'Unreadable recording'} /><h2>{session.name.replaceAll('-', ' ')}</h2><p>{sessionDate(session.date)} · {session.activity}</p></div><a class="secondary-button" href={sessionDownload(session.file)} download={session.file}><ArrowDownToLine size={17} /> Download CSV</a></div>
    <div class="report-tabs" role="tablist" aria-label="Session report sections">
      {#each tabs as title, index}<button id={`report-tab-${index}`} role="tab" aria-selected={activeTab === index} aria-controls="report-panel" tabindex={activeTab === index ? 0 : -1} class:active={activeTab === index} onclick={() => activeTab = index} onkeydown={(event) => changeTab(event, index)}>{title}</button>{/each}
    </div>
    <div id="report-panel" role="tabpanel" aria-labelledby={`report-tab-${activeTab}`} tabindex="0" class="report-panel">
      {#if activeTab === 0}
        <div class="spec-grid">
          <GlassCard class="spec-card"><div class="spec-label"><Activity size={17} />Recorded poses</div><strong>{session.frames.toLocaleString()}</strong><p>Unique inference frames</p></GlassCard>
          <GlassCard class="spec-card"><div class="spec-label"><Clock3 size={17} />Sample span</div><strong>{sessionDuration(session.sample_span_ms)}</strong><p>First to last captured pose</p></GlassCard>
          <GlassCard class="spec-card"><div class="spec-label"><ScanLine size={17} />Landmarks</div><strong>{session.landmarks}</strong><p>Distinct points present in this file</p></GlassCard>
        </div>
        <GlassCard class="capture-summary"><span class="summary-symbol"><FileText size={28} /></span><div><p class="eyebrow">What this recording tells us</p><h3>{session.frames ? 'Movement captured. Detail preserved.' : 'No usable pose samples yet.'}</h3><p>{session.frames ? 'Your raw landmark coordinates and timestamps are available in the CSV. Analytical gait measurements are not calculated by the current recorder.' : 'Try another capture with good lighting and your whole body visible.'}</p></div></GlassCard>
        <HelpAccordion items={[{ question: 'Why is sample span shorter than my test?', answer: 'Only new detected poses are saved. Camera warm-up, missed detection, or stopping early can shorten the interval between the first and last recorded samples. This is not a measure of tracking accuracy.' }, { question: 'What does a saved recording mean?', answer: 'The CSV is available on this device. Saved does not certify a complete test, sufficient tracking quality, or a clinical finding.' }]} />
      {:else if activeTab === 1}
        <GlassCard class="analysis-placeholder"><p class="eyebrow">Joint kinematics</p><h3>Angles need a little more context.</h3><p>Coordinates are captured. Joint-angle calculations and their validation are not yet connected.</p><div class="pending-metrics">{#each ['Hip angle', 'Knee flexion', 'Ankle angle'] as metric}<div><span>{metric}</span><strong>—</strong><small>Not calculated</small></div>{/each}</div></GlassCard>
        <HelpAccordion items={[{ question: 'How will joint angles be calculated?', answer: 'Angles can be derived from adjacent landmark segments, but a reliable result also needs confidence filtering, camera-view assumptions, and validation. The current UI does not estimate or invent these values.' }]} />
      {:else if activeTab === 2}
        <GlassCard class="analysis-placeholder"><p class="eyebrow">Left & right</p><h3>Balance, measured with care.</h3><p>A symmetry score needs reliable step events and a defined comparison method. Those measurements are not available yet.</p><div class="symmetry-pair"><div><span>LEFT</span><strong>—</strong><small>Awaiting step analysis</small></div><span class="symmetry-divider"><Activity size={28} /></span><div><span>RIGHT</span><strong>—</strong><small>Awaiting step analysis</small></div></div><StatusPill label="Not calculated" /></GlassCard>
        <HelpAccordion items={[{ question: 'Does no score mean my gait is asymmetric?', answer: 'No. It means this software has not calculated a symmetry measurement. Missing analysis is not a finding about your movement.' }]} />
      {:else}
        <GlassCard><p class="eyebrow">The original capture</p><h3>Recording details</h3><dl class="recording-details"><div><dt>File</dt><dd>{session.file}</dd></div><div><dt>First sample</dt><dd>{sessionDate(session.date)}</dd></div><div><dt>Activity</dt><dd>{session.activity}</dd></div><div><dt>Pose frames</dt><dd>{session.frames}</dd></div><div><dt>File size</dt><dd>{(session.size / 1024).toFixed(1)} KB</dd></div><div><dt>Storage</dt><dd>Local · data/sessions</dd></div></dl></GlassCard>
        <HelpAccordion items={[{ question: 'What is inside the CSV?', answer: 'Each row describes one landmark: its name, normalized x/y/z coordinates, confidence values, frame index, and timestamps. This is recorded data, not a medical interpretation.' }]} />
      {/if}
    </div>
  {/if}
</div>
