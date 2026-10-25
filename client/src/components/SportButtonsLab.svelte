<script lang="ts">
  let { onTrigger = (name: string) => {} }: { onTrigger?: (name: string) => void } = $props();

  // Magnetic button state
  let magBtn = $state<HTMLButtonElement>();
  let magX = $state(0);
  let magY = $state(0);
  let isHoveredMag = $state(false);

  function handleMagMouseMove(e: MouseEvent) {
    if (!magBtn) return;
    const rect = magBtn.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const distanceX = e.clientX - centerX;
    const distanceY = e.clientY - centerY;

    magX = distanceX * 0.35;
    magY = distanceY * 0.35;
  }

  function handleMagMouseEnter() {
    isHoveredMag = true;
  }

  function handleMagMouseLeave() {
    isHoveredMag = false;
    magX = 0;
    magY = 0;
  }

  // 3D Tilt button state
  let tiltBtn = $state<HTMLButtonElement>();
  let tiltX = $state(0);
  let tiltY = $state(0);
  let isHoveredTilt = $state(false);

  function handleTiltMouseMove(e: MouseEvent) {
    if (!tiltBtn) return;
    const rect = tiltBtn.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const xPct = (x / rect.width - 0.5) * 2;
    const yPct = (y / rect.height - 0.5) * 2;

    tiltX = -yPct * 14;
    tiltY = xPct * 14;
  }

  function handleTiltMouseEnter() {
    isHoveredTilt = true;
  }

  function handleTiltMouseLeave() {
    isHoveredTilt = false;
    tiltX = 0;
    tiltY = 0;
  }

  // Shake button trigger
  let shaking = $state(false);
  function triggerShake() {
    shaking = true;
    setTimeout(() => { shaking = false; }, 450);
  }

  let toast = $state<string | null>(null);
  let toastTimer: any = null;

  function handleClick(btnName: string) {
    onTrigger(btnName);
    toast = `Executed: ${btnName}`;
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast = null; }, 2200);
  }
</script>

<div class="buttons-showcase">
  <div class="showcase-header">
    <div class="badge">
      <span class="live-pulse"></span>
      <span>GAIT KINETIC ENGINE // 7 TACTILE BUTTONS</span>
    </div>
    <h3 class="showcase-title">TACTILE GAIT TEST CONTROLS</h3>
    <p class="showcase-sub">
      Micro-interactions engineered for athletic diagnostic tools. Tuned with fast spring physics, high-contrast cyan, and tactile feedback.
    </p>
  </div>

  <div class="buttons-grid">
    <!-- 1. MAGNETIC BUTTON -->
    <div class="button-card">
      <div class="card-meta">
        <span class="num">01</span>
        <span class="tag">MAGNETIC PULL</span>
      </div>
      <p class="desc">Cursor pulls the button with elastic spring physics. Main test launcher.</p>
      <div class="btn-stage">
        <button
          bind:this={magBtn}
          class="btn-magnetic"
          style:transform={`translate3d(${magX}px, ${magY}px, 0px) scale(${isHoveredMag ? 1.06 : 1})`}
          onmousemove={handleMagMouseMove}
          onmouseenter={handleMagMouseEnter}
          onmouseleave={handleMagMouseLeave}
          onclick={() => handleClick('1. Magnetic Button')}
        >
          <span class="btn-label">START 60S GAIT TEST</span>
          <span class="btn-arrow">→</span>
        </button>
      </div>
      <div class="card-footnote">PRIMARY ACTION · SPRING STIFFNESS 400</div>
    </div>

    <!-- 2. FILL / WIPE BUTTON -->
    <div class="button-card">
      <div class="card-meta">
        <span class="num">02</span>
        <span class="tag">CYAN ENERGY WIPE</span>
      </div>
      <p class="desc">Vibrant cyan #00C8F5 sweeps across on hover like an active camera buffer.</p>
      <div class="btn-stage">
        <button
          class="btn-fill-wipe"
          onclick={() => handleClick('2. Fill / Wipe Button')}
        >
          <span class="wipe-bg"></span>
          <span class="wipe-content">
            <span>ANALYZE ASYMMETRY</span>
            <b>⚡</b>
          </span>
        </button>
      </div>
      <div class="card-footnote">SECONDARY ACTION · 0.32S SPRING EASE</div>
    </div>

    <!-- 3. 3D TILT + SHADOW -->
    <div class="button-card">
      <div class="card-meta">
        <span class="num">03</span>
        <span class="tag">3D TILT + ELEVATION</span>
      </div>
      <p class="desc">Tilts in 3D perspective with soft cyan depth shadow on hover.</p>
      <div class="btn-stage perspective-stage">
        <button
          bind:this={tiltBtn}
          class="btn-3d-tilt"
          class:hovered={isHoveredTilt}
          style:transform={`perspective(600px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) translateZ(${isHoveredTilt ? 10 : 0}px)`}
          onmousemove={handleTiltMouseMove}
          onmouseenter={handleTiltMouseEnter}
          onmouseleave={handleTiltMouseLeave}
          onclick={() => handleClick('3. 3D Tilt + Shadow')}
        >
          <span class="tilt-tag">KINETIC MATRIX</span>
          <span class="tilt-title">CADENCE // 188 SPM</span>
        </button>
      </div>
      <div class="card-footnote">ELEVATED CARD · 0 20PX 40PX SHADOW</div>
    </div>

    <!-- 4. TEXT SLIDE BUTTON -->
    <div class="button-card">
      <div class="card-meta">
        <span class="num">04</span>
        <span class="tag">SPLIT SCOREBOARD SLIDE</span>
      </div>
      <p class="desc">Scoreboard slide: "TEST PROTOCOL" moves up, "RECORD STRIDE →" drops in.</p>
      <div class="btn-stage">
        <button
          class="btn-text-slide"
          onclick={() => handleClick('4. Text Slide Button')}
        >
          <div class="slide-viewport">
            <span class="slide-first">TEST PROTOCOL</span>
            <span class="slide-second">RECORD STRIDE →</span>
          </div>
        </button>
      </div>
      <div class="card-footnote">DUAL-SPAN Y-AXIS SCOREBOARD SHIFT</div>
    </div>

    <!-- 5. STRETCH / LIQUID BUTTON -->
    <div class="button-card">
      <div class="card-meta">
        <span class="num">05</span>
        <span class="tag">ELASTIC SQUASH & STRETCH</span>
      </div>
      <p class="desc">Rubber ball deformation: scaleX 1.18, scaleY 0.88 with athletic bounce.</p>
      <div class="btn-stage">
        <button
          class="btn-liquid"
          onclick={() => handleClick('5. Liquid / Stretch Button')}
        >
          <span class="ball-dot"></span>
          <span>LAUNCH 3-CAMERA SYNC</span>
        </button>
      </div>
      <div class="card-footnote">SPRING OVERSHOOT (0.34, 1.56, 0.64, 1)</div>
    </div>

    <!-- 6. BORDER RUN / NEON TRACE -->
    <div class="button-card">
      <div class="card-meta">
        <span class="num">06</span>
        <span class="tag">CYAN BORDER TRACE</span>
      </div>
      <p class="desc">Rotating cyan gradient tracks the perimeter like an active laser scanner.</p>
      <div class="btn-stage">
        <button
          class="btn-neon-trace"
          onclick={() => handleClick('6. Neon Trace Button')}
        >
          <span class="trace-glow"></span>
          <span class="trace-inner">
            <span class="live-dot"></span>
            <span>LIVE 33-POINT SKELETON</span>
          </span>
        </button>
      </div>
      <div class="card-footnote">ROTATING CONIC GRADIENT SCANNER</div>
    </div>

    <!-- 7. PUNCH / SHAKE BUTTON -->
    <div class="button-card">
      <div class="card-meta">
        <span class="num">07</span>
        <span class="tag">PEAK FORCE PUNCH</span>
      </div>
      <p class="desc">High-frequency vibration punch on hover signaling peak propulsion force.</p>
      <div class="btn-stage">
        <button
          class="btn-punch"
          class:shaking={shaking}
          onmouseenter={triggerShake}
          onclick={() => handleClick('7. Punch / Shake Button')}
        >
          <span>PEAK PROPULSION STRIKE</span>
          <span class="impact">⚡</span>
        </button>
      </div>
      <div class="card-footnote">ATHLETIC INTENSITY VIBRATION KEYFRAMES</div>
    </div>
  </div>

  {#if toast}
    <div class="action-toast">
      <span>⚡ {toast}</span>
    </div>
  {/if}
</div>

<style>
  .buttons-showcase {
    background: #ffffff;
    border: 1px solid #e1e7e9;
    border-radius: 12px;
    padding: clamp(24px, 4vw, 44px);
    margin: 20px 0;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 30px rgba(7, 23, 28, 0.04);
  }

  .buttons-showcase::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #07171c, #00c8f5, #07171c);
  }

  .showcase-header {
    margin-bottom: 32px;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #dff8ff;
    border: 1px solid rgba(0, 200, 245, 0.3);
    padding: 6px 14px;
    border-radius: 9999px;
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    letter-spacing: 0.12em;
    color: #0877aa;
    margin-bottom: 14px;
    font-weight: 700;
  }

  .live-pulse {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #00c8f5;
    box-shadow: 0 0 8px #00c8f5;
    animation: pulse 1.4s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.8); }
  }

  .showcase-title {
    margin: 0;
    font-family: 'Manrope', 'Anton', sans-serif;
    font-size: clamp(26px, 4vw, 42px);
    font-weight: 800;
    letter-spacing: -0.04em;
    color: #07171c;
    line-height: 1;
  }

  .showcase-sub {
    margin: 12px 0 0;
    color: #607075;
    font-size: 15px;
    max-width: 640px;
    line-height: 1.5;
  }

  .buttons-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 18px;
  }

  .button-card {
    background: #f8f8f6;
    border: 1px solid #e1e7e9;
    border-radius: 8px;
    padding: 22px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 250px;
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
  }

  .button-card:hover {
    border-color: #00c8f5;
    box-shadow: 0 8px 24px rgba(0, 200, 245, 0.08);
  }

  .card-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .card-meta .num {
    font-family: 'Anton', sans-serif;
    font-size: 20px;
    color: #07171c;
  }

  .card-meta .tag {
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    letter-spacing: 0.1em;
    color: #0877aa;
    font-weight: 700;
  }

  .desc {
    margin: 0 0 16px;
    font-size: 13px;
    color: #607075;
    line-height: 1.45;
  }

  .btn-stage {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px 0;
  }

  .perspective-stage {
    perspective: 600px;
  }

  .card-footnote {
    font-family: 'Oswald', sans-serif;
    font-size: 10px;
    letter-spacing: 0.08em;
    color: #8c9ea4;
    border-top: 1px solid #e5ecee;
    padding-top: 10px;
  }

  /* 1. MAGNETIC BUTTON */
  .btn-magnetic {
    background: #07171c;
    color: #ffffff;
    border: none;
    padding: 14px 24px;
    font-family: 'Manrope', sans-serif;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.06em;
    display: inline-flex;
    align-items: center;
    gap: 14px;
    cursor: pointer;
    border-radius: 4px;
    box-shadow: 0 6px 18px rgba(7, 23, 28, 0.15);
    transition: transform 0.15s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.2s ease, background 0.2s ease;
    will-change: transform;
  }

  .btn-magnetic:hover {
    background: #14282f;
    box-shadow: 0 12px 28px rgba(7, 23, 28, 0.25);
  }

  .btn-magnetic .btn-arrow {
    font-size: 20px;
    line-height: 1;
    color: #00c8f5;
    transition: transform 0.2s ease;
  }

  .btn-magnetic:hover .btn-arrow {
    transform: translateX(4px);
  }

  /* 2. FILL / WIPE BUTTON */
  .btn-fill-wipe {
    position: relative;
    overflow: hidden;
    background: transparent;
    border: 2px solid #07171c;
    color: #07171c;
    padding: 13px 26px;
    font-family: 'Manrope', sans-serif;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.06em;
    cursor: pointer;
    border-radius: 4px;
  }

  .wipe-bg {
    position: absolute;
    inset: 0;
    background: #00c8f5;
    transform: translateX(-100%);
    transition: transform 0.32s cubic-bezier(0.22, 1, 0.36, 1);
    z-index: 1;
  }

  .wipe-content {
    position: relative;
    z-index: 2;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    transition: color 0.25s ease;
  }

  .btn-fill-wipe:hover .wipe-bg {
    transform: translateX(0);
  }

  .btn-fill-wipe:hover .wipe-content {
    color: #07171c;
  }

  /* 3. 3D TILT BUTTON */
  .btn-3d-tilt {
    background: #ffffff;
    border: 1px solid #c2d8dc;
    color: #07171c;
    padding: 14px 24px;
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
    cursor: pointer;
    transform-style: preserve-3d;
    box-shadow: 0 4px 14px rgba(7, 23, 28, 0.06);
    transition: transform 0.12s ease-out, box-shadow 0.2s ease, border-color 0.2s ease;
  }

  .btn-3d-tilt.hovered {
    box-shadow: 0 16px 36px rgba(0, 200, 245, 0.25);
    border-color: #00c8f5;
  }

  .tilt-tag {
    font-family: 'Oswald', sans-serif;
    font-size: 10px;
    color: #0877aa;
    letter-spacing: 0.12em;
    font-weight: 700;
  }

  .tilt-title {
    font-family: 'Anton', sans-serif;
    font-size: 16px;
    letter-spacing: 0.04em;
  }

  /* 4. TEXT SLIDE BUTTON */
  .btn-text-slide {
    background: #07171c;
    border: none;
    color: #ffffff;
    padding: 12px 26px;
    border-radius: 4px;
    cursor: pointer;
    overflow: hidden;
    height: 50px;
    box-shadow: 0 6px 16px rgba(7, 23, 28, 0.12);
  }

  .slide-viewport {
    position: relative;
    height: 24px;
    overflow: hidden;
  }

  .slide-first, .slide-second {
    display: block;
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 14px;
    letter-spacing: 0.08em;
    line-height: 24px;
    transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .slide-second {
    position: absolute;
    inset: 0;
    transform: translateY(100%);
    color: #00c8f5;
  }

  .btn-text-slide:hover .slide-first {
    transform: translateY(-100%);
  }

  .btn-text-slide:hover .slide-second {
    transform: translateY(0);
  }

  /* 5. LIQUID SQUASH & STRETCH */
  .btn-liquid {
    background: #00c8f5;
    color: #07171c;
    border: none;
    padding: 13px 24px;
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 0.06em;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    border-radius: 9999px;
    box-shadow: 0 6px 20px rgba(0, 200, 245, 0.3);
    transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
    transform-origin: center;
  }

  .btn-liquid .ball-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #07171c;
  }

  .btn-liquid:hover {
    transform: scaleX(1.16) scaleY(0.88);
    box-shadow: 0 10px 28px rgba(0, 200, 245, 0.45);
  }

  /* 6. NEON TRACE BUTTON */
  .btn-neon-trace {
    position: relative;
    background: transparent;
    border: none;
    padding: 2px;
    border-radius: 6px;
    cursor: pointer;
    overflow: hidden;
    display: inline-block;
  }

  .trace-glow {
    position: absolute;
    inset: -150%;
    background: conic-gradient(from 0deg, transparent 0deg, #00c8f5 90deg, #07171c 180deg, transparent 270deg);
    animation: rotateTrace 3s linear infinite;
  }

  @keyframes rotateTrace {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .trace-inner {
    position: relative;
    background: #ffffff;
    color: #07171c;
    padding: 13px 24px;
    border-radius: 4px;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 0.06em;
    z-index: 2;
  }

  .trace-inner .live-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #00c8f5;
    box-shadow: 0 0 6px #00c8f5;
  }

  /* 7. PUNCH / SHAKE BUTTON */
  .btn-punch {
    background: #07171c;
    color: #ffffff;
    border: none;
    padding: 13px 26px;
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 0.06em;
    cursor: pointer;
    border-radius: 4px;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    box-shadow: 0 6px 18px rgba(7, 23, 28, 0.15);
    transition: transform 0.1s ease;
  }

  .btn-punch.shaking {
    animation: punchShake 0.4s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
  }

  @keyframes punchShake {
    10%, 90% { transform: translate3d(-3px, 0, 0) scale(1.04); }
    20%, 80% { transform: translate3d(4px, 0, 0) scale(1.04); }
    30%, 50%, 70% { transform: translate3d(-4px, 0, 0) scale(1.04); }
    40%, 60% { transform: translate3d(4px, 0, 0) scale(1.04); }
    100% { transform: translate3d(0, 0, 0) scale(1); }
  }

  .action-toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: #07171c;
    color: #ffffff;
    padding: 12px 24px;
    border-radius: 9999px;
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 0.04em;
    box-shadow: 0 10px 30px rgba(7, 23, 28, 0.25);
    border: 1px solid #00c8f5;
    z-index: 100;
    animation: toastPop 0.25s cubic-bezier(0.22, 1, 0.36, 1);
  }

  @keyframes toastPop {
    from { opacity: 0; transform: translateY(16px) scale(0.9); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }
</style>
