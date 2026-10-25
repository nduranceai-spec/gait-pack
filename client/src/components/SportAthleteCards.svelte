<script lang="ts">
  interface Athlete {
    id: string;
    number: string;
    name: string;
    sport: string;
    role: string;
    color: string;
    accent: string;
    stats: {
      speed: string;
      cadence: string;
      stride: string;
      symmetry: string;
      confidence: string;
      grf: string;
    };
    flipped: boolean;
  }

  let athletes = $state<Athlete[]>([
    {
      id: 'ath-1',
      number: '01',
      name: 'SPRINT ACCELERATION',
      sport: '100M / TRACK SPRINTERS',
      role: 'EXPLOSIVE DRIVE & PROJECTION',
      color: '#ffffff',
      accent: '#00c8f5',
      stats: {
        speed: '37.4 km/h',
        cadence: '194 SPM',
        stride: '2.38 m',
        symmetry: '98.8%',
        confidence: '99.4%',
        grf: '3.8 BW',
      },
      flipped: false,
    },
    {
      id: 'ath-2',
      number: '02',
      name: 'MARATHON EFFICIENCY',
      sport: 'LONG DISTANCE & PACE',
      role: 'AEROBIC ECONOMY & OSCILLATION',
      color: '#ffffff',
      accent: '#07171c',
      stats: {
        speed: '21.2 km/h',
        cadence: '182 SPM',
        stride: '1.85 m',
        symmetry: '99.2%',
        confidence: '99.6%',
        grf: '2.4 BW',
      },
      flipped: false,
    },
    {
      id: 'ath-3',
      number: '03',
      name: 'ACL RETURN-TO-PLAY',
      sport: 'POST-SURGICAL REHAB',
      role: 'BILATERAL LOAD BALANCE',
      color: '#ffffff',
      accent: '#00c8f5',
      stats: {
        speed: '14.8 km/h',
        cadence: '176 SPM',
        stride: '1.62 m',
        symmetry: '96.5%',
        confidence: '99.1%',
        grf: '2.1 BW',
      },
      flipped: false,
    },
  ]);

  let cardTilts = $state<Record<string, { x: number; y: number }>>({});

  function handleMouseMove(e: MouseEvent, id: string) {
    const card = e.currentTarget as HTMLElement;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const xPct = (x / rect.width - 0.5) * 2;
    const yPct = (y / rect.height - 0.5) * 2;

    cardTilts[id] = {
      x: -yPct * 12,
      y: xPct * 12,
    };
  }

  function handleMouseLeave(id: string) {
    cardTilts[id] = { x: 0, y: 0 };
  }

  function toggleFlip(id: string) {
    const ath = athletes.find((a) => a.id === id);
    if (ath) ath.flipped = !ath.flipped;
  }
</script>

<div class="cards-section">
  <div class="cards-header">
    <div>
      <span class="eyebrow">ATHLETE KINEMATIC PROFILES</span>
      <h3 class="title">GAIT TEST BENCHMARKS & 3D CARDS</h3>
    </div>
    <p class="subtitle">
      Hover to inspect 3D perspective depth. Click <strong>FLIP STATS</strong> to view live MediaPipe 33-point gait parameters and symmetry metrics.
    </p>
  </div>

  <div class="cards-grid">
    {#each athletes as athlete (athlete.id)}
      {@const tilt = cardTilts[athlete.id] ?? { x: 0, y: 0 }}
      <div
        class="card-perspective-wrapper"
        role="presentation"
        onmousemove={(e) => handleMouseMove(e, athlete.id)}
        onmouseleave={() => handleMouseLeave(athlete.id)}
      >
        <div
          class="card-inner"
          class:is-flipped={athlete.flipped}
          style:transform={`perspective(1000px) rotateX(${tilt.x}deg) rotateY(${tilt.y + (athlete.flipped ? 180 : 0)}deg)`}
        >
          <!-- FRONT FACE -->
          <div class="card-face card-front" style:--card-accent={athlete.accent}>
            <div class="face-top">
              <span class="jersey-num">#{athlete.number}</span>
              <span class="sport-badge">{athlete.sport}</span>
            </div>

            <div class="silhouette-area">
              <div class="hologram-ring"></div>
              <div class="hologram-ring inner"></div>
              <div class="giant-num">{athlete.number}</div>
              <div class="pulse-marker"></div>
            </div>

            <div class="face-bottom">
              <div>
                <span class="athlete-role">{athlete.role}</span>
                <h4 class="athlete-name">{athlete.name}</h4>
              </div>
              <div class="quick-metric">
                <span class="m-val">{athlete.stats.speed}</span>
                <span class="m-lbl">PEAK SPRINT</span>
              </div>
            </div>

            <button
              class="flip-trigger"
              onclick={(e) => { e.stopPropagation(); toggleFlip(athlete.id); }}
            >
              <span>FLIP STATS ↻</span>
            </button>
          </div>

          <!-- BACK FACE (STATS) -->
          <div class="card-face card-back" style:--card-accent={athlete.accent}>
            <div class="back-top">
              <span class="back-title">{athlete.name} // METRICS</span>
              <button
                class="back-close"
                onclick={(e) => { e.stopPropagation(); toggleFlip(athlete.id); }}
              >
                ✕ FRONT
              </button>
            </div>

            <div class="stats-matrix">
              <div class="stat-cell">
                <span class="s-label">MAX VELOCITY</span>
                <strong class="s-val cyan-accent">{athlete.stats.speed}</strong>
              </div>
              <div class="stat-cell">
                <span class="s-label">CADENCE</span>
                <strong class="s-val">{athlete.stats.cadence}</strong>
              </div>
              <div class="stat-cell">
                <span class="s-label">STRIDE LENGTH</span>
                <strong class="s-val">{athlete.stats.stride}</strong>
              </div>
              <div class="stat-cell">
                <span class="s-label">BILATERAL SYMMETRY</span>
                <strong class="s-val cyan-accent">{athlete.stats.symmetry}</strong>
              </div>
              <div class="stat-cell">
                <span class="s-label">MEDIAPIPE TRACKING</span>
                <strong class="s-val">{athlete.stats.confidence}</strong>
              </div>
              <div class="stat-cell">
                <span class="s-label">PEAK IMPACT GRF</span>
                <strong class="s-val">{athlete.stats.grf}</strong>
              </div>
            </div>

            <div class="telemetry-bar">
              <div class="bar-fill" style:width={athlete.stats.symmetry}></div>
            </div>

            <div class="back-foot">
              <span>LOCAL 33-POINT AI EXTRACTION</span>
              <span class="live-dot"></span>
            </div>
          </div>
        </div>
      </div>
    {/each}
  </div>
</div>

<style>
  .cards-section {
    padding: 24px 0;
  }

  .cards-header {
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

  .subtitle strong {
    color: #07171c;
  }

  .cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 24px;
  }

  .card-perspective-wrapper {
    perspective: 1000px;
    height: 480px;
  }

  .card-inner {
    position: relative;
    width: 100%;
    height: 100%;
    transform-style: preserve-3d;
    transition: transform 0.65s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .card-face {
    position: absolute;
    inset: 0;
    border-radius: 10px;
    background: #ffffff;
    border: 1px solid #e1e7e9;
    padding: 24px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    backface-visibility: hidden;
    overflow: hidden;
    box-shadow: 0 12px 36px rgba(7, 23, 28, 0.06);
  }

  .face-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 2;
  }

  .jersey-num {
    font-family: 'Anton', sans-serif;
    font-size: 24px;
    color: #07171c;
  }

  .sport-badge {
    background: #f1f5f7;
    color: #07171c;
    font-family: 'Oswald', sans-serif;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.1em;
    padding: 4px 10px;
    border-radius: 9999px;
  }

  .silhouette-area {
    position: relative;
    flex: 1;
    display: grid;
    place-items: center;
    overflow: hidden;
  }

  .hologram-ring {
    position: absolute;
    width: 180px;
    height: 180px;
    border-radius: 50%;
    border: 1px dashed rgba(0, 200, 245, 0.4);
    animation: rotateRing 14s linear infinite;
  }

  .hologram-ring.inner {
    width: 120px;
    height: 120px;
    border: 1px solid rgba(7, 23, 28, 0.1);
    animation: rotateRing 8s linear infinite reverse;
  }

  @keyframes rotateRing {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .giant-num {
    font-family: 'Anton', sans-serif;
    font-size: 150px;
    line-height: 1;
    color: #e5edf0;
    user-select: none;
    letter-spacing: -0.06em;
  }

  .pulse-marker {
    position: absolute;
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #00c8f5;
    box-shadow: 0 0 12px #00c8f5;
    animation: pulseMark 2s ease infinite;
  }

  @keyframes pulseMark {
    0%, 100% { transform: scale(1); opacity: 0.9; }
    50% { transform: scale(1.6); opacity: 0.3; }
  }

  .face-bottom {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 12px;
    z-index: 2;
  }

  .athlete-role {
    font-family: 'Oswald', sans-serif;
    font-size: 10px;
    letter-spacing: 0.1em;
    color: #607075;
    display: block;
    margin-bottom: 2px;
    font-weight: 700;
  }

  .athlete-name {
    margin: 0;
    font-family: 'Manrope', 'Anton', sans-serif;
    font-size: 19px;
    font-weight: 800;
    color: #07171c;
    letter-spacing: -0.02em;
  }

  .quick-metric {
    text-align: right;
  }

  .m-val {
    font-family: 'Anton', sans-serif;
    font-size: 24px;
    color: #07171c;
    display: block;
    line-height: 1;
  }

  .m-lbl {
    font-family: 'Oswald', sans-serif;
    font-size: 9px;
    letter-spacing: 0.08em;
    color: #607075;
  }

  .flip-trigger {
    border: none;
    background: #07171c;
    color: #ffffff;
    padding: 11px;
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 12px;
    letter-spacing: 0.08em;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.2s ease, transform 0.2s ease;
  }

  .flip-trigger:hover {
    background: #152d35;
    transform: translateY(-1px);
  }

  /* BACK FACE */
  .card-back {
    transform: rotateY(180deg);
    border-color: #00c8f5;
  }

  .back-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 12px;
    border-bottom: 1px solid #e1e7e9;
  }

  .back-title {
    font-family: 'Manrope', 'Anton', sans-serif;
    font-size: 15px;
    font-weight: 800;
    color: #07171c;
  }

  .back-close {
    background: #f1f5f7;
    border: 1px solid #dce4e6;
    color: #07171c;
    font-family: 'Oswald', sans-serif;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.08em;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
  }

  .stats-matrix {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 18px 0;
  }

  .stat-cell {
    background: #f8f8f6;
    padding: 12px;
    border-radius: 6px;
    border-left: 3px solid #00c8f5;
  }

  .s-label {
    display: block;
    font-family: 'Oswald', sans-serif;
    font-size: 9px;
    letter-spacing: 0.1em;
    color: #607075;
    margin-bottom: 3px;
  }

  .s-val {
    font-family: 'Anton', sans-serif;
    font-size: 18px;
    color: #07171c;
    letter-spacing: 0.03em;
  }

  .cyan-accent {
    color: #0098be !important;
  }

  .telemetry-bar {
    width: 100%;
    height: 4px;
    background: #e1e7e9;
    border-radius: 9999px;
    overflow: hidden;
    margin-top: auto;
    margin-bottom: 12px;
  }

  .bar-fill {
    height: 100%;
    background: #00c8f5;
    border-radius: 9999px;
  }

  .back-foot {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'Oswald', sans-serif;
    font-size: 10px;
    color: #607075;
    letter-spacing: 0.08em;
  }

  .live-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #00c8f5;
    box-shadow: 0 0 6px #00c8f5;
  }
</style>
