<script lang="ts">
  import { ArrowRight, ArrowUpRight, Camera, Footprints, ShieldCheck } from '@lucide/svelte';
  import GlassCard from '../components/GlassCard.svelte';
  import MotionFigure from '../components/MotionFigure.svelte';
  import SessionList from '../components/SessionList.svelte';
  import HelpAccordion from '../components/HelpAccordion.svelte';
  import type { Session } from '../lib/types';
  let { sessions, loading, error, onRetry, onStart, onHistory, onOpen }: {
    sessions: Session[]; loading: boolean; error: string; onRetry: () => void;
    onStart: () => void; onHistory: () => void; onOpen: (session: Session) => void;
  } = $props();
</script>

<div class="page-stack">
  <section class="editorial-hero">
    <div class="editorial-copy">
      <span class="edition-label">Your movement workspace</span>
      <h2>Capture movement.<br />Keep every detail.</h2>
      <p>Connect a camera, record a guided gait session, and keep your landmark data on this device.</p>
      <div class="hero-actions">
        <button class="primary-button" onclick={onStart}>Begin a gait test <ArrowRight size={18} /></button>
        <button class="text-button" onclick={onHistory}>Explore recordings <ArrowUpRight size={17} /></button>
      </div>
      <div class="hero-footnote"><ShieldCheck size={14} /> Local capture. Your pace. Your data.</div>
    </div>
    <GlassCard class="body-showcase" elevated>
      <div class="showcase-top"><span>Capture model</span><span>Body + hands</span></div>
      <div class="body-orbit orbit-outer"></div><div class="body-orbit orbit-inner"></div>
      <div class="body-illustration"><MotionFigure /></div>
      <div class="annotation annotation-lower"><Footprints size={16} /><div><small>Body landmarks</small><strong>22 recording points</strong></div></div>
      <div class="showcase-caption"><span>Illustration · not live data</span><span>MediaPipe</span></div>
    </GlassCard>
  </section>

  <div class="spec-grid" aria-label="Recording overview">
    <div class="spec-card"><div class="spec-label">Saved recordings</div><strong>{loading || error ? '—' : sessions.filter(session => session.status === 'saved').length}<span>sessions</span></strong><p>{error ? 'Library unavailable' : 'From your local recording library'}</p></div>
    <div class="spec-card"><div class="spec-label">Capture window</div><strong>60<span>seconds</span></strong><p>Save earlier whenever you need</p></div>
    <div class="spec-card"><div class="spec-label">Private storage</div><strong>Local<span>CSV</span></strong><p>Coordinates only. No saved video.</p></div>
  </div>

  <section class="journey-section">
    <div class="section-heading"><div><p class="eyebrow">Simple by design</p><h3>From first step to recorded movement.</h3></div><span class="section-index">01 — 03</span></div>
    <div class="journey-grid">
      <article><span class="step-number">01</span><Camera size={22} /><h4>Find your frame</h4><p>Connect your camera and check your whole body is visible.</p></article>
      <article><span class="step-number">02</span><Footprints size={22} /><h4>Move naturally</h4><p>Start a 60-second capture at a comfortable, unhurried pace.</p></article>
      <article><span class="step-number">03</span><ArrowUpRight size={22} /><h4>Keep the detail</h4><p>Review the saved session and download your landmark data.</p></article>
    </div>
  </section>

  <div class="dashboard-bottom">
    <GlassCard class="history-preview">
      <div class="section-heading"><div><p class="eyebrow">Your movement library</p><h3>Recent recordings</h3></div><button class="text-button" onclick={onHistory}>View all <ArrowUpRight size={16} /></button></div>
      {#if loading}<p class="quiet-message" role="status">Loading your recordings…</p>
      {:else if error}<div class="inline-notice" role="status"><p>{error}</p><button class="text-button" onclick={onRetry}>Try again <ArrowRight size={15} /></button></div>
      {:else if sessions.length}<SessionList sessions={sessions.slice(0, 3)} {onOpen} />
      {:else}<div class="empty-library"><Footprints size={28} /><h4>Your first step starts here.</h4><p>Saved recordings will appear after your first test.</p><button class="text-button" onclick={onStart}>Set up camera <ArrowRight size={16} /></button></div>{/if}
    </GlassCard>
    <GlassCard class="assurance-card">
      <ShieldCheck size={26} strokeWidth={1.3} /><p class="eyebrow">Thoughtful by design</p><h3>Clarity, without<br />the guesswork.</h3><p>Recording is live. Measurements appear only when an analysis method is available.</p>
      <HelpAccordion items={[{ question: 'What is saved?', answer: 'The recorder saves body landmark coordinates and timestamps to a local CSV. It does not save camera video. Face landmarks are excluded by the default recording profile.' }, { question: 'Is this a medical report?', answer: 'No. This workspace captures movement data. Joint angles, gait symmetry, and clinical interpretations are not currently calculated.' }]} />
    </GlassCard>
  </div>
</div>
