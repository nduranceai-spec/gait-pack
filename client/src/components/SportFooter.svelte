<script lang="ts">
  let { onStartTest = () => {} }: { onStartTest?: () => void } = $props();

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
</script>

<footer class="sports-footer">
  <div class="footer-inner">
    <!-- Top Product Action Card -->
    <div class="footer-cta-banner">
      <div>
        <span class="cta-eyebrow">READY TO BENCHMARK YOUR ATHLETIC MOVEMENT?</span>
        <h2 class="cta-heading">Capture movement. Keep every detail.</h2>
      </div>
      <button class="footer-cta-btn" onclick={onStartTest}>
        <span>START LIVE GAIT TEST →</span>
      </button>
    </div>

    <!-- Main Footer Grid -->
    <div class="footer-main-grid">
      <div class="footer-col brand-col">
        <div class="footer-logo">
          <span class="logo-bolt">⚡</span>
          <span class="logo-title">GAIT KINETIC PRO</span>
        </div>
        <p class="brand-desc">
          Computer vision gait analysis and athletic biomechanics diagnostics platform.
          Powered by 33-point MediaPipe pose landmarking and local CSV data sovereignty.
        </p>
        <div class="engine-status">
          <span class="status-light"></span>
          <span>LOCAL MEDIAPIPE AI + PYTHON API 8765 ONLINE</span>
        </div>
      </div>

      <div class="footer-col">
        <h5 class="col-title">PRODUCT</h5>
        <ul class="col-links">
          <li><a href="#hero-section">Overview & Stride Hero</a></li>
          <li><a href="#three-section">3D Kinetic Avatar</a></li>
          <li><a href="#buttons-section">7 Tactile Controls</a></li>
          <li><a href="#athletes-section">Athlete Profiles</a></li>
          <li><a href="#timeline-section">Kinematic Timeline</a></li>
        </ul>
      </div>

      <div class="footer-col">
        <h5 class="col-title">BIOMECHANICS</h5>
        <ul class="col-links">
          <li><a href="#stats-section">Bilateral Gait Symmetry</a></li>
          <li><a href="#stats-section">Stride Cadence (SPM)</a></li>
          <li><a href="#stats-section">Ground Reaction Force</a></li>
          <li><a href="#protocols-section">4 Standard Test Protocols</a></li>
          <li><a href="#protocols-section">Sprint Benchmarks</a></li>
        </ul>
      </div>

      <div class="footer-col">
        <h5 class="col-title">PLATFORM</h5>
        <ul class="col-links">
          <li><span>MediaPipe Tasks Vision 0.10</span></li>
          <li><span>Three.js 0.186 WebGL</span></li>
          <li><span>Lenis Smooth Scroll Engine</span></li>
          <li><span>Local CSV Coordinate Export</span></li>
          <li><span>Sub-millimeter Joint Precision</span></li>
        </ul>
      </div>
    </div>

    <!-- Bottom Copyright & Back to Top -->
    <div class="footer-bottom">
      <p class="copy">
        © 2026 GAIT KINETIC PRO · ENGINEERED FOR ELITE ATHLETES, CLINICIANS & BIOMECHANISTS.
      </p>
      <button class="back-to-top" onclick={scrollToTop}>
        <span>BACK TO TOP ↑</span>
      </button>
    </div>
  </div>
</footer>

<style>
  .sports-footer {
    background: #ffffff;
    border-top: 1px solid #e1e7e9;
    color: #07171c;
    padding: clamp(40px, 6vw, 70px) clamp(18px, 4vw, 42px) 40px;
    position: relative;
    overflow: hidden;
  }

  .footer-inner {
    max-width: 1440px;
    margin: 0 auto;
  }

  /* CTA Banner */
  .footer-cta-banner {
    background: #07171c;
    border-radius: 8px;
    padding: clamp(28px, 4vw, 50px);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 28px;
    margin-bottom: 50px;
    color: #ffffff;
    position: relative;
    overflow: hidden;
  }

  .footer-cta-banner::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: #00c8f5;
  }

  .cta-eyebrow {
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    letter-spacing: 0.12em;
    color: #00c8f5;
    display: block;
    margin-bottom: 6px;
    font-weight: 700;
  }

  .cta-heading {
    margin: 0;
    font-family: 'Manrope', 'Anton', sans-serif;
    font-size: clamp(28px, 4.5vw, 52px);
    font-weight: 800;
    letter-spacing: -0.04em;
    color: #ffffff;
    line-height: 1;
  }

  .footer-cta-btn {
    background: #00c8f5;
    color: #07171c;
    border: none;
    padding: 16px 32px;
    font-family: 'Manrope', sans-serif;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 0.06em;
    border-radius: 4px;
    cursor: pointer;
    box-shadow: 0 8px 24px rgba(0, 200, 245, 0.3);
    transition: transform 0.2s cubic-bezier(0.22, 1, 0.36, 1), background 0.2s ease;
  }

  .footer-cta-btn:hover {
    background: #38d6fc;
    transform: translateY(-2px);
  }

  /* Main Grid */
  .footer-main-grid {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1.2fr;
    gap: clamp(24px, 4vw, 50px);
    padding-bottom: 40px;
    border-bottom: 1px solid #eef3f5;
  }

  .footer-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
  }

  .logo-bolt {
    font-size: 24px;
    color: #00c8f5;
  }

  .logo-title {
    font-family: 'Anton', sans-serif;
    font-size: 22px;
    letter-spacing: 0.02em;
    color: #07171c;
  }

  .brand-desc {
    color: #607075;
    font-size: 14px;
    line-height: 1.6;
    max-width: 360px;
    margin: 0 0 18px;
  }

  .engine-status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #dff8ff;
    padding: 6px 12px;
    border-radius: 9999px;
    font-family: 'Oswald', sans-serif;
    font-size: 10px;
    letter-spacing: 0.08em;
    color: #0877aa;
    font-weight: 700;
  }

  .status-light {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #00c8f5;
    box-shadow: 0 0 6px #00c8f5;
  }

  .col-title {
    margin: 0 0 16px;
    font-family: 'Anton', sans-serif;
    font-size: 14px;
    letter-spacing: 0.06em;
    color: #07171c;
  }

  .col-links {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    gap: 10px;
  }

  .col-links a, .col-links span {
    color: #607075;
    font-size: 13px;
    text-decoration: none;
    transition: color 0.2s ease;
  }

  .col-links a:hover {
    color: #00c8f5;
  }

  /* Bottom */
  .footer-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
    padding-top: 24px;
  }

  .copy {
    margin: 0;
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    letter-spacing: 0.08em;
    color: #8c9ea4;
  }

  .back-to-top {
    background: transparent;
    border: 1px solid #dce4e6;
    color: #07171c;
    padding: 6px 14px;
    border-radius: 4px;
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .back-to-top:hover {
    border-color: #07171c;
    background: #f8f8f6;
  }

  @media (max-width: 960px) {
    .footer-main-grid {
      grid-template-columns: 1fr 1fr;
    }
  }

  @media (max-width: 600px) {
    .footer-main-grid {
      grid-template-columns: 1fr;
    }
    .footer-cta-btn {
      width: 100%;
    }
  }
</style>
