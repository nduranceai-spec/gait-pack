<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';
  import { ScrollTrigger } from 'gsap/ScrollTrigger';
  import SportBallScene from './SportBallScene.svelte';

  gsap.registerPlugin(ScrollTrigger);

  let {
    onStartTest = () => {},
    onExplore3D = () => {},
  }: {
    onStartTest?: () => void;
    onExplore3D?: () => void;
  } = $props();

  let heroTitle = $state<HTMLHeadingElement>();
  let heroOrb = $state<HTMLDivElement>();

  onMount(() => {
    let cleanup = () => {};

    if (heroTitle && heroOrb) {
      // Parallax scrub on scroll
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: '.hero-container',
          start: 'top top',
          end: 'bottom top',
          scrub: 0.6,
        },
      });

      tl.to('.hero-title-main', { y: -60, opacity: 0.35, ease: 'none' }, 0);
      tl.to('.hero-3d-col', { y: 40, scale: 0.96, ease: 'none' }, 0);

      cleanup = () => {
        ScrollTrigger.getAll().forEach((st) => st.kill());
      };
    }

    return () => cleanup();
  });

  function scrollDown() {
    const el = document.getElementById('three-section');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }
</script>

<section class="hero-container" id="hero-section">
  <div class="hero-inner">
    <!-- Left Column: Typography & CTAs -->
    <div class="hero-text-col">
      <div class="eyebrow-pill">
        <i class="dot"></i>
        <span>ATHLETE GAIT TESTING & BIOMECHANICS LAB</span>
      </div>

      <h1 class="hero-title-main" bind:this={heroTitle}>
        <span class="line-1">Test your</span>
        <span class="line-2"><em>stride.</em></span>
      </h1>

      <p class="hero-subtext">
        Real-time 33-point MediaPipe computer vision, bilateral asymmetry detection, and contact-time diagnostics.
        Engineered for elite sprinters, distance runners, and sports physical therapists.
      </p>

      <div class="hero-cta-group">
        <!-- Main Product CTA (Black with Cyan Arrow) -->
        <button class="hero-primary-btn" onclick={onStartTest}>
          <span>START A GAIT TEST</span>
          <span class="cyan-arr">→</span>
        </button>

        <button class="hero-secondary-btn" onclick={scrollDown}>
          <span>EXPLORE 3D AVATAR</span>
          <span class="arr">↓</span>
        </button>
      </div>

      <!-- Quick specs pill matching clean aesthetic -->
      <div class="hero-specs-grid">
        <div class="spec-item">
          <strong>33 LANDMARKS</strong>
          <span>FULL-BODY MESH</span>
        </div>
        <div class="spec-sep"></div>
        <div class="spec-item">
          <strong>LOCAL CAPTURE</strong>
          <span>ZERO CLOUD LATENCY</span>
        </div>
        <div class="spec-sep"></div>
        <div class="spec-item">
          <strong>&lt; 2.0% ASYMMETRY</strong>
          <span>ACCURACY TOLERANCE</span>
        </div>
      </div>
    </div>

    <!-- Right Column: Interactive 3D Sports Model with Clean White Elevation -->
    <div class="hero-3d-col" bind:this={heroOrb}>
      <div class="arena-card">
        <div class="card-head">
          <span class="head-label">3D Kinetic Model</span>
          <span class="head-tag">MediaPipe Vision</span>
        </div>
        <SportBallScene />
        <div class="card-foot">
          <span>DRAG 360° · REAL-TIME SURFACE SHADERS</span>
          <span class="status-live">ONLINE</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Bottom Scroll Down Indicator -->
  <button class="scroll-indicator" onclick={scrollDown} aria-label="Scroll to features">
    <span class="indicator-text">EXPLORE LAB</span>
    <span class="indicator-mouse">
      <span class="mouse-wheel"></span>
    </span>
  </button>
</section>

<style>
  .hero-container {
    position: relative;
    min-height: calc(100vh - 80px);
    display: flex;
    flex-direction: column;
    justify-content: center;
    background: #f8f8f6;
    padding: clamp(30px, 5vw, 60px) clamp(18px, 4vw, 42px) 80px;
    overflow: hidden;
  }

  .hero-inner {
    position: relative;
    z-index: 2;
    max-width: 1440px;
    margin: 0 auto;
    width: 100%;
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: clamp(24px, 5vw, 60px);
    align-items: center;
  }

  .hero-text-col {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }

  .eyebrow-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 24px;
    color: #607075;
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.12em;
  }

  .eyebrow-pill .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #00c8f5;
    box-shadow: 0 0 0 5px rgba(0, 200, 245, 0.16);
  }

  .hero-title-main {
    margin: 0;
    font-family: 'Manrope', 'Anton', sans-serif;
    font-size: clamp(64px, 10vw, 150px);
    line-height: 0.82;
    letter-spacing: -0.06em;
    font-weight: 800;
    color: #07171c;
  }

  .line-1 {
    display: block;
    color: #07171c;
  }

  .line-2 em {
    font-style: normal;
    color: #00c8f5;
    display: block;
  }

  .hero-subtext {
    margin: 28px 0 36px;
    color: #607075;
    font-size: clamp(16px, 1.7vw, 20px);
    line-height: 1.5;
    max-width: 540px;
    letter-spacing: -0.02em;
  }

  .hero-cta-group {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 16px;
    margin-bottom: 40px;
  }

  .hero-primary-btn {
    background: #07171c;
    border: none;
    color: #f8f8f6;
    padding: 16px 28px;
    border-radius: 2px;
    cursor: pointer;
    font-family: 'Manrope', sans-serif;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 0.08em;
    display: inline-flex;
    align-items: center;
    gap: 20px;
    box-shadow: 0 10px 24px rgba(7, 23, 28, 0.15);
    transition: transform 0.22s cubic-bezier(0.22, 1, 0.36, 1), background 0.22s ease;
  }

  .hero-primary-btn:hover {
    background: #152d35;
    transform: translateY(-2px);
  }

  .cyan-arr {
    color: #00c8f5;
    font-size: 22px;
    line-height: 0.5;
  }

  .hero-secondary-btn {
    background: transparent;
    border: 1px solid #adbabb;
    color: #07171c;
    padding: 16px 24px;
    border-radius: 2px;
    font-family: 'Manrope', sans-serif;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.08em;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .hero-secondary-btn:hover {
    border-color: #07171c;
    background: #ffffff;
    transform: translateY(-2px);
  }

  .hero-secondary-btn .arr {
    font-size: 16px;
    transition: transform 0.2s ease;
  }

  .hero-secondary-btn:hover .arr {
    transform: translateY(3px);
  }

  /* Specs row under hero */
  .hero-specs-grid {
    display: flex;
    align-items: center;
    gap: 22px;
    padding: 14px 20px;
    background: #ffffff;
    border: 1px solid #e1e7e9;
    border-radius: 6px;
    box-shadow: 0 4px 16px rgba(7, 23, 28, 0.04);
  }

  .spec-item {
    display: flex;
    flex-direction: column;
  }

  .spec-item strong {
    font-family: 'Anton', sans-serif;
    font-size: 16px;
    color: #07171c;
    letter-spacing: 0.04em;
    line-height: 1;
  }

  .spec-item span {
    font-family: 'Oswald', sans-serif;
    font-size: 9px;
    color: #607075;
    letter-spacing: 0.08em;
    margin-top: 3px;
  }

  .spec-sep {
    width: 1px;
    height: 22px;
    background: #e1e7e9;
  }

  /* 3D Col in Light & Clean */
  .hero-3d-col {
    position: relative;
    width: 100%;
    min-height: 480px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .arena-card {
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 480px;
    border-radius: 12px;
    background: #ffffff;
    border: 1px solid #dce4e6;
    overflow: hidden;
    box-shadow: 0 16px 45px rgba(7, 23, 28, 0.08);
    display: flex;
    flex-direction: column;
  }

  .card-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 20px;
    border-bottom: 1px solid #e8eff0;
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    letter-spacing: 0.1em;
  }

  .head-label {
    color: #607075;
  }

  .head-tag {
    background: #dff8ff;
    color: #0877aa;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 700;
  }

  .card-foot {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    border-top: 1px solid #e8eff0;
    font-family: 'Oswald', sans-serif;
    font-size: 10px;
    letter-spacing: 0.1em;
    color: #607075;
  }

  .status-live {
    color: #00c8f5;
    font-weight: 700;
  }

  /* Scroll Indicator */
  .scroll-indicator {
    position: absolute;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: transparent;
    border: none;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    z-index: 10;
  }

  .indicator-text {
    font-family: 'Oswald', sans-serif;
    font-size: 10px;
    letter-spacing: 0.14em;
    color: #8c9ea4;
    transition: color 0.2s ease;
  }

  .indicator-mouse {
    width: 20px;
    height: 32px;
    border: 2px solid #aebabc;
    border-radius: 12px;
    position: relative;
    display: flex;
    justify-content: center;
  }

  .mouse-wheel {
    width: 3px;
    height: 6px;
    background: #00c8f5;
    border-radius: 2px;
    position: absolute;
    top: 6px;
    animation: mouseScroll 1.6s infinite;
  }

  @keyframes mouseScroll {
    0% { transform: translateY(0); opacity: 1; }
    100% { transform: translateY(12px); opacity: 0; }
  }

  .scroll-indicator:hover .indicator-text {
    color: #07171c;
  }

  @media (max-width: 992px) {
    .hero-inner {
      grid-template-columns: 1fr;
    }
    .hero-3d-col {
      min-height: 400px;
    }
  }
</style>
