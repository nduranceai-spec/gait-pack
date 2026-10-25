<script lang="ts">
  import { onMount } from 'svelte';

  let container = $state<HTMLDivElement>();
  let hasAnimated = $state(false);

  // Animated counters
  let valVelocity = $state(0);
  let valCadence = $state(0);
  let valSymmetry = $state(0);
  let valContactTime = $state(0);

  function animateCounters() {
    if (hasAnimated) return;
    hasAnimated = true;

    const duration = 1800;
    const start = performance.now();

    function update(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);

      valVelocity = Math.round(ease * 374) / 10;
      valCadence = Math.round(ease * 192);
      valSymmetry = Math.round(ease * 988) / 10;
      valContactTime = Math.round(ease * 182);

      if (progress < 1) {
        requestAnimationFrame(update);
      }
    }

    requestAnimationFrame(update);
  }

  onMount(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          animateCounters();
        }
      },
      { threshold: 0.25 }
    );

    if (container) observer.observe(container);

    return () => observer.disconnect();
  });
</script>

<div class="stats-section" bind:this={container}>
  <div class="stats-header">
    <div>
      <span class="eyebrow">ATHLETIC TELEMETRY ENGINE</span>
      <h3 class="title">BIOMECHANICAL PERFORMANCE STATS</h3>
    </div>
    <p class="subtitle">
      Automated gait symmetry extraction, concentric kinetic efficiency rings, and stance phase load distribution.
    </p>
  </div>

  <!-- Primary Counters Grid -->
  <div class="counters-grid">
    <!-- 1. Velocity -->
    <div class="counter-card">
      <div class="card-top">
        <span class="card-tag">TOP VELOCITY</span>
        <span class="card-icon">⚡</span>
      </div>
      <div class="card-value">
        <strong>{valVelocity.toFixed(1)}</strong>
        <span class="unit">km/h</span>
      </div>
      <div class="card-bar">
        <div class="bar-fill" style:width={`${(valVelocity / 40) * 100}%`}></div>
      </div>
      <p class="card-footnote">Sprint phase acceleration</p>
    </div>

    <!-- 2. Cadence -->
    <div class="counter-card">
      <div class="card-top">
        <span class="card-tag">STRIDE CADENCE</span>
        <span class="card-icon">🔄</span>
      </div>
      <div class="card-value">
        <strong>{valCadence}</strong>
        <span class="unit">SPM</span>
      </div>
      <div class="card-bar">
        <div class="bar-fill" style:width={`${(valCadence / 220) * 100}%`}></div>
      </div>
      <p class="card-footnote">Optimal 180-195 target zone</p>
    </div>

    <!-- 3. Symmetry -->
    <div class="counter-card">
      <div class="card-top">
        <span class="card-tag">GAIT SYMMETRY</span>
        <span class="card-icon">⚖️</span>
      </div>
      <div class="card-value">
        <strong class="cyan-txt">{valSymmetry.toFixed(1)}</strong>
        <span class="unit">%</span>
      </div>
      <div class="card-bar">
        <div class="bar-fill cyan-fill" style:width={`${valSymmetry}%`}></div>
      </div>
      <p class="card-footnote">Near-perfect bilateral balance</p>
    </div>

    <!-- 4. Contact Time -->
    <div class="counter-card">
      <div class="card-top">
        <span class="card-tag">GROUND CONTACT</span>
        <span class="card-icon">⏱️</span>
      </div>
      <div class="card-value">
        <strong>{valContactTime}</strong>
        <span class="unit">ms</span>
      </div>
      <div class="card-bar">
        <div class="bar-fill" style:width={`${(valContactTime / 300) * 100}%`}></div>
      </div>
      <p class="card-footnote">Elite elastic recoil efficiency</p>
    </div>
  </div>

  <!-- Deep Biomechanical Charts: Progress Rings + Force Distribution -->
  <div class="deep-stats-row">
    <!-- Concentric Progress Rings -->
    <div class="rings-card">
      <h4 class="card-heading">KINETIC EFFICIENCY RINGS</h4>
      <div class="rings-wrapper">
        <svg viewBox="0 0 200 200" class="rings-svg">
          <!-- Background Circles -->
          <circle cx="100" cy="100" r="80" class="ring-bg" stroke-width="10" />
          <circle cx="100" cy="100" r="62" class="ring-bg" stroke-width="10" />
          <circle cx="100" cy="100" r="44" class="ring-bg" stroke-width="10" />

          <!-- Outer Ring: Symmetry 98% (Cyan) -->
          <circle
            cx="100" cy="100" r="80"
            class="ring-active"
            stroke="#00c8f5"
            stroke-width="10"
            stroke-dasharray="502"
            stroke-dashoffset={hasAnimated ? 502 * (1 - 0.988) : 502}
          />
          <!-- Middle Ring: Cadence 88% (Dark Ink) -->
          <circle
            cx="100" cy="100" r="62"
            class="ring-active"
            stroke="#07171c"
            stroke-width="10"
            stroke-dasharray="389"
            stroke-dashoffset={hasAnimated ? 389 * (1 - 0.88) : 389}
          />
          <!-- Inner Ring: Ground Efficiency 84% (Sky Blue) -->
          <circle
            cx="100" cy="100" r="44"
            class="ring-active"
            stroke="#82d4fb"
            stroke-width="10"
            stroke-dasharray="276"
            stroke-dashoffset={hasAnimated ? 276 * (1 - 0.84) : 276}
          />
        </svg>

        <div class="rings-legend">
          <div class="legend-item">
            <span class="leg-color" style:background="#00c8f5"></span>
            <span class="leg-name">Symmetry: <strong>98.8%</strong></span>
          </div>
          <div class="legend-item">
            <span class="leg-color" style:background="#07171c"></span>
            <span class="leg-name">Cadence: <strong>192 SPM</strong></span>
          </div>
          <div class="legend-item">
            <span class="leg-color" style:background="#82d4fb"></span>
            <span class="leg-name">Contact Ratio: <strong>182 ms</strong></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Biomechanical Bar Chart: Force Distribution Across Gait Cycle -->
    <div class="bars-card">
      <h4 class="card-heading">GAIT LOAD DISTRIBUTION (0% - 100% STRIDE)</h4>
      <div class="bars-chart">
        {#each [
          { label: '0%', val: 32, note: 'HEEL' },
          { label: '15%', val: 68, note: 'LOADING' },
          { label: '30%', val: 92, note: 'MIDSTANCE' },
          { label: '50%', val: 100, note: 'TERMINAL' },
          { label: '65%', val: 84, note: 'PRE-SWING' },
          { label: '80%', val: 42, note: 'INITIAL' },
          { label: '100%', val: 26, note: 'FLOAT' },
        ] as bar}
          <div class="chart-col">
            <span class="col-val">{hasAnimated ? `${bar.val}%` : '0%'}</span>
            <div class="col-track">
              <div
                class="col-fill"
                style:height={hasAnimated ? `${bar.val}%` : '0%'}
              ></div>
            </div>
            <span class="col-lbl">{bar.label}</span>
            <span class="col-note">{bar.note}</span>
          </div>
        {/each}
      </div>
    </div>
  </div>
</div>

<style>
  .stats-section {
    padding: 24px 0;
  }

  .stats-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: 20px;
    margin-bottom: 32px;
  }

  .eyebrow {
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    letter-spacing: 0.12em;
    color: #0877aa;
    font-weight: 700;
    display: block;
    margin-bottom: 6px;
  }

  .title {
    margin: 0;
    font-family: 'Manrope', 'Anton', sans-serif;
    font-size: clamp(26px, 4vw, 42px);
    font-weight: 800;
    letter-spacing: -0.04em;
    color: #07171c;
    line-height: 1;
  }

  .subtitle {
    margin: 0;
    color: #607075;
    font-size: 14px;
    max-width: 440px;
    line-height: 1.5;
  }

  /* Counters Grid */
  .counters-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 18px;
    margin-bottom: 24px;
  }

  .counter-card {
    background: #ffffff;
    border: 1px solid #e1e7e9;
    border-radius: 8px;
    padding: 22px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 160px;
    box-shadow: 0 6px 20px rgba(7, 23, 28, 0.04);
    transition: transform 0.22s cubic-bezier(0.22, 1, 0.36, 1), border-color 0.2s ease;
  }

  .counter-card:hover {
    transform: translateY(-3px);
    border-color: #00c8f5;
  }

  .card-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .card-tag {
    font-family: 'Oswald', sans-serif;
    font-size: 10px;
    letter-spacing: 0.1em;
    color: #607075;
    font-weight: 700;
  }

  .card-icon {
    font-size: 16px;
  }

  .card-value {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin: 12px 0 8px;
  }

  .card-value strong {
    font-family: 'Anton', sans-serif;
    font-size: 46px;
    line-height: 0.9;
    letter-spacing: -0.02em;
    color: #07171c;
  }

  .cyan-txt {
    color: #0098be !important;
  }

  .card-value .unit {
    font-family: 'Oswald', sans-serif;
    font-size: 13px;
    letter-spacing: 0.08em;
    color: #607075;
  }

  .card-bar {
    width: 100%;
    height: 4px;
    background: #e9eff1;
    border-radius: 9999px;
    overflow: hidden;
    margin-bottom: 8px;
  }

  .bar-fill {
    height: 100%;
    background: #07171c;
    transition: width 1.8s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .cyan-fill {
    background: #00c8f5 !important;
  }

  .card-footnote {
    margin: 0;
    font-size: 12px;
    color: #8c9ea4;
  }

  /* Deep Stats */
  .deep-stats-row {
    display: grid;
    grid-template-columns: 1fr 1.4fr;
    gap: 20px;
  }

  .rings-card, .bars-card {
    background: #ffffff;
    border: 1px solid #e1e7e9;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 6px 20px rgba(7, 23, 28, 0.04);
  }

  .card-heading {
    margin: 0 0 18px;
    font-family: 'Manrope', 'Anton', sans-serif;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #07171c;
  }

  .rings-wrapper {
    display: flex;
    align-items: center;
    gap: 24px;
    flex-wrap: wrap;
    justify-content: center;
  }

  .rings-svg {
    width: 160px;
    height: 160px;
    transform: rotate(-90deg);
  }

  .ring-bg {
    fill: none;
    stroke: #e8eff0;
  }

  .ring-active {
    fill: none;
    stroke-linecap: round;
    transition: stroke-dashoffset 1.8s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .rings-legend {
    display: grid;
    gap: 12px;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .leg-color {
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }

  .leg-name {
    font-family: 'Manrope', sans-serif;
    font-size: 13px;
    color: #607075;
  }

  .leg-name strong {
    color: #07171c;
    font-family: 'Anton', sans-serif;
    letter-spacing: 0.02em;
  }

  /* Bar Chart */
  .bars-chart {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 12px;
    height: 180px;
    align-items: end;
    padding-top: 20px;
  }

  .chart-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 100%;
    justify-content: flex-end;
  }

  .col-val {
    font-family: 'Anton', sans-serif;
    font-size: 11px;
    color: #0098be;
    margin-bottom: 6px;
  }

  .col-track {
    width: 100%;
    max-width: 24px;
    height: 110px;
    background: #eef3f5;
    border-radius: 4px;
    display: flex;
    align-items: flex-end;
    overflow: hidden;
  }

  .col-fill {
    width: 100%;
    background: linear-gradient(180deg, #00c8f5, #07171c);
    border-radius: 4px;
    transition: height 1.6s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .col-lbl {
    font-family: 'Anton', sans-serif;
    font-size: 12px;
    color: #07171c;
    margin-top: 8px;
  }

  .col-note {
    font-family: 'Oswald', sans-serif;
    font-size: 9px;
    color: #8c9ea4;
    letter-spacing: 0.06em;
  }

  @media (max-width: 860px) {
    .deep-stats-row {
      grid-template-columns: 1fr;
    }
  }
</style>
