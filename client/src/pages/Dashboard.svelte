<script lang="ts">
  import SportHero from '../components/SportHero.svelte';
  import SportButtonsLab from '../components/SportButtonsLab.svelte';
  import SportAthleteCards from '../components/SportAthleteCards.svelte';
  import SportTimeline from '../components/SportTimeline.svelte';
  import SportStats from '../components/SportStats.svelte';
  import SportLeaderboard from '../components/SportLeaderboard.svelte';
  import SportBallScene from '../components/SportBallScene.svelte';
  import SportFooter from '../components/SportFooter.svelte';
  import SessionList from '../components/SessionList.svelte';
  import type { Session } from '../lib/types';

  let {
    sessions = [],
    loading = false,
    error = '',
    onRetry = () => {},
    onStart = () => {},
    onHistory = () => {},
    onOpen = (_session: Session) => {},
  }: {
    sessions: Session[];
    loading: boolean;
    error: string;
    onRetry: () => void;
    onStart: () => void;
    onHistory: () => void;
    onOpen: (session: Session) => void;
  } = $props();

  function handleButtonAction(btnName: string) {
    if (btnName.includes('Magnetic') || btnName.includes('START') || btnName.includes('LAUNCH')) {
      onStart();
    }
  }
</script>

<div class="sports-portal">
  <!-- 1. Fullscreen Hero: "Test your stride." -->
  <SportHero onStartTest={onStart} />

  <!-- Main Content Flow -->
  <main class="portal-content">
    <!-- 2. 3D Kinetic Avatar Section -->
    <section class="section-block" id="three-section">
      <div class="section-title-wrap">
        <span class="sec-badge">THREE.JS 0.186 // KINETIC AVATAR VIEWER</span>
        <h2 class="sec-heading">3D ATHLETE MOTION VIEWER</h2>
        <p class="sec-desc">
          Drag to rotate 360° with dynamic physics damping, procedural shader maps, dual rim point lights, and kinetic orbital particles.
        </p>
      </div>

      <div class="arena-frame">
        <div class="arena-hud-top">
          <div class="hud-item">
            <span class="hud-dot"></span>
            <span>THREE.JS WEBGL 2.0 // HIGH PERFORMANCE</span>
          </div>
          <div class="hud-item">
            <span>60 FPS SMOOTH SCROLL & DAMPING</span>
          </div>
        </div>
        <div class="arena-inner-canvas">
          <SportBallScene />
        </div>
        <div class="arena-hud-bottom">
          <span>INTERACTIVE 3D MODEL · DRAG WITH MOUSE OR TOUCH</span>
          <button class="arena-scan-btn" onclick={onStart}>
            <span>CONTINUE TO CAMERAS →</span>
          </button>
        </div>
      </div>
    </section>

    <!-- 3. 7 Tactile Gait Test Controls -->
    <section class="section-block" id="buttons-section">
      <SportButtonsLab onTrigger={handleButtonAction} />
    </section>

    <!-- 4. Athlete Gait Benchmark Cards (3D Tilt + Flip) -->
    <section class="section-block" id="athletes-section">
      <SportAthleteCards />
    </section>

    <!-- 5. Kinematic Stride Phase Timeline -->
    <section class="section-block" id="timeline-section">
      <SportTimeline />
    </section>

    <!-- 6. Biomechanical Performance Stats & Rings -->
    <section class="section-block" id="stats-section">
      <SportStats />
    </section>

    <!-- 7. Gait Test Protocols & Benchmarks -->
    <section class="section-block" id="protocols-section">
      <SportLeaderboard onSelectProtocol={onStart} />
    </section>

    <!-- 8. Local Saved Recordings Shelf -->
    <section class="section-block library-shelf">
      <div class="shelf-header">
        <div>
          <span class="sec-badge">LOCAL SESSIONS</span>
          <h3 class="shelf-title">RECENT GAIT RECORDINGS</h3>
        </div>
        <div class="shelf-actions">
          <button class="shelf-btn-sec" onclick={onHistory}>VIEW ALL ({sessions.length})</button>
          <button class="shelf-btn-pri" onclick={onStart}>NEW GAIT TEST +</button>
        </div>
      </div>

      {#if loading}
        <div class="shelf-status"><p>Loading local session recordings…</p></div>
      {:else if error}
        <div class="shelf-status error">
          <p>{error}</p>
          <button onclick={onRetry}>Retry</button>
        </div>
      {:else if sessions.length > 0}
        <div class="shelf-list-wrap">
          <SessionList sessions={sessions.slice(0, 4)} {onOpen} />
        </div>
      {:else}
        <div class="shelf-empty">
          <span class="empty-icon">⚡</span>
          <h4>NO RECORDINGS YET</h4>
          <p>Record your first 60-second gait session with local 33-point MediaPipe AI detection.</p>
          <button class="start-first-btn" onclick={onStart}>START A GAIT TEST →</button>
        </div>
      {/if}
    </section>
  </main>

  <!-- 9. Clean Sports Footer -->
  <SportFooter onStartTest={onStart} />
</div>

<style>
  .sports-portal {
    background: #f8f8f6;
    color: #07171c;
    min-height: 100vh;
    overflow-x: hidden;
  }

  .portal-content {
    max-width: 1440px;
    margin: 0 auto;
    padding: 0 clamp(18px, 4vw, 42px);
  }

  .section-block {
    padding: clamp(36px, 5vw, 64px) 0;
    border-bottom: 1px solid #e5ecee;
  }

  .section-title-wrap {
    margin-bottom: 28px;
  }

  .sec-badge {
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    letter-spacing: 0.12em;
    color: #0877aa;
    font-weight: 700;
    display: block;
    margin-bottom: 6px;
  }

  .sec-heading {
    margin: 0 0 10px;
    font-family: 'Manrope', 'Anton', sans-serif;
    font-size: clamp(28px, 4.5vw, 48px);
    font-weight: 800;
    letter-spacing: -0.04em;
    color: #07171c;
    line-height: 1;
  }

  .sec-desc {
    margin: 0;
    color: #607075;
    font-size: 15px;
    max-width: 600px;
    line-height: 1.5;
  }

  /* 3D Arena Frame */
  .arena-frame {
    background: #ffffff;
    border: 1px solid #dce4e6;
    border-radius: 12px;
    overflow: hidden;
    position: relative;
    box-shadow: 0 12px 36px rgba(7, 23, 28, 0.06);
  }

  .arena-hud-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 20px;
    background: #f8f8f6;
    border-bottom: 1px solid #e8eff0;
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    letter-spacing: 0.1em;
    color: #607075;
  }

  .hud-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .hud-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #00c8f5;
    box-shadow: 0 0 6px #00c8f5;
  }

  .arena-inner-canvas {
    height: clamp(400px, 48vh, 520px);
    position: relative;
  }

  .arena-hud-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 14px;
    padding: 14px 20px;
    background: #f8f8f6;
    border-top: 1px solid #e8eff0;
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    letter-spacing: 0.08em;
    color: #607075;
  }

  .arena-scan-btn {
    background: #07171c;
    color: #ffffff;
    border: none;
    padding: 8px 18px;
    border-radius: 4px;
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 12px;
    letter-spacing: 0.06em;
    cursor: pointer;
    transition: background 0.2s ease, transform 0.2s ease;
  }

  .arena-scan-btn:hover {
    background: #14282f;
    transform: translateY(-2px);
  }

  /* Library Shelf */
  .library-shelf {
    border-bottom: none;
  }

  .shelf-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: 20px;
    margin-bottom: 24px;
  }

  .shelf-title {
    margin: 0;
    font-family: 'Manrope', 'Anton', sans-serif;
    font-size: clamp(24px, 3.5vw, 38px);
    font-weight: 800;
    letter-spacing: -0.04em;
    color: #07171c;
    line-height: 1;
  }

  .shelf-actions {
    display: flex;
    gap: 12px;
  }

  .shelf-btn-sec {
    background: transparent;
    border: 1px solid #adbabb;
    color: #07171c;
    padding: 8px 16px;
    border-radius: 4px;
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .shelf-btn-sec:hover {
    border-color: #07171c;
    background: #ffffff;
  }

  .shelf-btn-pri {
    background: #07171c;
    color: #ffffff;
    border: none;
    padding: 8px 18px;
    border-radius: 4px;
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 12px;
    letter-spacing: 0.06em;
    cursor: pointer;
    transition: transform 0.2s ease, background 0.2s ease;
  }

  .shelf-btn-pri:hover {
    background: #152d35;
    transform: translateY(-2px);
  }

  .shelf-status {
    padding: 40px;
    text-align: center;
    color: #607075;
    font-size: 14px;
  }

  .shelf-empty {
    text-align: center;
    padding: 50px 20px;
    background: #ffffff;
    border: 1px dashed #cdd8db;
    border-radius: 8px;
  }

  .empty-icon {
    font-size: 32px;
    color: #00c8f5;
    display: block;
    margin-bottom: 10px;
  }

  .shelf-empty h4 {
    margin: 0 0 8px;
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 20px;
    color: #07171c;
  }

  .shelf-empty p {
    margin: 0 0 20px;
    color: #607075;
    font-size: 14px;
  }

  .start-first-btn {
    background: #07171c;
    color: #ffffff;
    border: none;
    padding: 12px 26px;
    border-radius: 4px;
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 0.06em;
    cursor: pointer;
    box-shadow: 0 4px 14px rgba(7, 23, 28, 0.15);
    transition: transform 0.2s ease, background 0.2s ease;
  }

  .start-first-btn:hover {
    background: #152d35;
    transform: translateY(-2px);
  }
</style>
