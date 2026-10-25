<script lang="ts">
  import { onMount } from 'svelte';

  let {
    onStartScan = () => {},
    onGoToWorkspace = () => {},
  }: {
    onStartScan?: () => void;
    onGoToWorkspace?: () => void;
  } = $props();

  let scrollProgress = $state(0);
  let navHidden = $state(false);
  let lastScrollY = 0;

  onMount(() => {
    function handleScroll() {
      const currentScrollY = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      scrollProgress = docHeight > 0 ? (currentScrollY / docHeight) * 100 : 0;

      if (currentScrollY > 120 && currentScrollY > lastScrollY) {
        navHidden = true;
      } else {
        navHidden = false;
      }
      lastScrollY = currentScrollY;
    }

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  });

  function scrollTo(id: string) {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  }
</script>

<!-- Top Scroll Progress Bar -->
<div class="top-progress-bar" style:width={`${scrollProgress}%`}></div>

<!-- Athlete Gait Telemetry Marquee Ticker -->
<div class="top-ticker" aria-label="Athlete Gait Telemetry Ticker">
  <div class="ticker-track">
    <div class="ticker-group">
      <span>⚡ STRIDE CADENCE: <strong>188 SPM</strong></span>
      <span class="sep">/</span>
      <span>🔥 KNEE FLEXION: <strong>64.2°</strong></span>
      <span class="sep">/</span>
      <span>⏱️ GROUND CONTACT: <strong>182 ms</strong></span>
      <span class="sep">/</span>
      <span>⚖️ BILATERAL ASYMMETRY: <strong>&lt; 1.6%</strong></span>
      <span class="sep">/</span>
      <span>✨ MEDIAPIPE AI POSE: <strong>33 SKELETAL POINTS ACTIVE</strong></span>
      <span class="sep">/</span>
      <span>🏃 VELOCITY BENCHMARK: <strong>9.82 m/s</strong></span>
      <span class="sep">/</span>
      <span>🎯 TEST WINDOWS: <strong>30s · 60s · 120s</strong></span>
      <span class="sep">/</span>
    </div>
    <!-- Duplicate for infinite seamless scroll -->
    <div class="ticker-group" aria-hidden="true">
      <span>⚡ STRIDE CADENCE: <strong>188 SPM</strong></span>
      <span class="sep">/</span>
      <span>🔥 KNEE FLEXION: <strong>64.2°</strong></span>
      <span class="sep">/</span>
      <span>⏱️ GROUND CONTACT: <strong>182 ms</strong></span>
      <span class="sep">/</span>
      <span>⚖️ BILATERAL ASYMMETRY: <strong>&lt; 1.6%</strong></span>
      <span class="sep">/</span>
      <span>✨ MEDIAPIPE AI POSE: <strong>33 SKELETAL POINTS ACTIVE</strong></span>
      <span class="sep">/</span>
      <span>🏃 VELOCITY BENCHMARK: <strong>9.82 m/s</strong></span>
      <span class="sep">/</span>
      <span>🎯 TEST WINDOWS: <strong>30s · 60s · 120s</strong></span>
      <span class="sep">/</span>
    </div>
  </div>
</div>

<!-- Main Clean Sports Navbar -->
<header class="sports-nav" class:nav-hidden={navHidden}>
  <div class="nav-inner">
    <div class="nav-brand">
      <span class="brand-logo">⚡</span>
      <div class="brand-text">
        <span class="main-word">GAIT</span>
        <span class="sub-word">KINETIC PRO // ATHLETE LAB</span>
      </div>
    </div>

    <nav class="nav-links">
      <button onclick={() => scrollTo('hero-section')}>OVERVIEW</button>
      <button onclick={() => scrollTo('three-section')}>3D AVATAR</button>
      <button onclick={() => scrollTo('buttons-section')}>7 BUTTONS</button>
      <button onclick={() => scrollTo('athletes-section')}>ATHLETES</button>
      <button onclick={() => scrollTo('timeline-section')}>TIMELINE</button>
      <button onclick={() => scrollTo('stats-section')}>METRICS</button>
      <button onclick={() => scrollTo('protocols-section')}>PROTOCOLS</button>
    </nav>

    <div class="nav-actions">
      <button class="workspace-btn" onclick={onGoToWorkspace}>
        <span>SAVED SESSIONS</span>
      </button>
      <button class="nav-cta" onclick={onStartScan}>
        <span class="pulse-indicator"></span>
        <span>START GAIT TEST</span>
        <span class="cta-arr">→</span>
      </button>
    </div>
  </div>
</header>

<style>
  .top-progress-bar {
    position: fixed;
    top: 0;
    left: 0;
    height: 4px;
    background: #00c8f5;
    box-shadow: 0 0 10px rgba(0, 200, 245, 0.5);
    z-index: 1000;
    pointer-events: none;
    transition: width 0.1s linear;
  }

  /* Marquee Ticker */
  .top-ticker {
    background: #07171c;
    color: #ffffff;
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    letter-spacing: 0.12em;
    padding: 8px 0;
    overflow: hidden;
    white-space: nowrap;
    position: relative;
    z-index: 99;
  }

  .ticker-track {
    display: flex;
    width: max-content;
    animation: tickerLoop 26s linear infinite;
  }

  .ticker-group {
    display: flex;
    align-items: center;
    gap: 18px;
    padding-right: 18px;
  }

  .ticker-group strong {
    color: #00c8f5;
    font-family: 'Anton', sans-serif;
    font-size: 13px;
    letter-spacing: 0.05em;
  }

  .sep {
    color: #2e3e44;
  }

  @keyframes tickerLoop {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
  }

  /* Main Nav */
  .sports-nav {
    position: sticky;
    top: 0;
    z-index: 90;
    background: rgba(248, 248, 246, 0.92);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid rgba(7, 23, 28, 0.08);
    transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .sports-nav.nav-hidden {
    transform: translateY(-100%);
  }

  .nav-inner {
    max-width: 1440px;
    margin: 0 auto;
    padding: 14px clamp(18px, 4vw, 42px);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
  }

  .nav-brand {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .brand-logo {
    font-size: 24px;
    color: #00c8f5;
  }

  .brand-text {
    display: flex;
    flex-direction: column;
  }

  .main-word {
    font-family: 'Anton', sans-serif;
    font-size: 24px;
    letter-spacing: 0.02em;
    color: #07171c;
    line-height: 1;
  }

  .sub-word {
    font-family: 'Oswald', sans-serif;
    font-size: 9px;
    letter-spacing: 0.16em;
    color: #607075;
  }

  .nav-links {
    display: flex;
    align-items: center;
    gap: 24px;
  }

  .nav-links button {
    background: transparent;
    border: none;
    color: #607075;
    font-family: 'Oswald', sans-serif;
    font-size: 12px;
    letter-spacing: 0.12em;
    cursor: pointer;
    padding: 6px 0;
    position: relative;
    transition: color 0.2s ease;
  }

  .nav-links button:hover {
    color: #07171c;
  }

  .nav-links button::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 0;
    height: 2px;
    background: #00c8f5;
    transition: width 0.2s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .nav-links button:hover::after {
    width: 100%;
  }

  .nav-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .workspace-btn {
    background: transparent;
    border: 1px solid rgba(7, 23, 28, 0.2);
    color: #07171c;
    padding: 8px 16px;
    border-radius: 4px;
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    letter-spacing: 0.1em;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .workspace-btn:hover {
    border-color: #00c8f5;
    color: #00c8f5;
  }

  .nav-cta {
    background: #07171c;
    color: #ffffff;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    font-family: 'Anton', sans-serif;
    font-size: 14px;
    letter-spacing: 0.06em;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    box-shadow: 0 4px 14px rgba(7, 23, 28, 0.15);
    transition: all 0.2s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .nav-cta:hover {
    background: #14282f;
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(7, 23, 28, 0.25);
  }

  .pulse-indicator {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #00c8f5;
    box-shadow: 0 0 8px #00c8f5;
    animation: ctaPulse 1.4s infinite;
  }

  @keyframes ctaPulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.3; transform: scale(0.7); }
  }

  .cta-arr {
    color: #00c8f5;
    font-size: 18px;
    line-height: 1;
  }

  @media (max-width: 992px) {
    .nav-links {
      display: none;
    }
  }
</style>
