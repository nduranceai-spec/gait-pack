<script lang="ts">
  let { onSelectProtocol = () => {} }: { onSelectProtocol?: () => void } = $props();

  let activeTab = $state<'protocols' | 'benchmarks'>('protocols');

  const protocols = [
    {
      id: 'proto-1',
      event: 'CLINICAL BASELINE',
      name: 'NORMAL GAIT WALK',
      venue: 'STANDARD 10M INDOOR PATH',
      duration: '60 SECONDS',
      status: 'RECOMMENDED',
      statusColor: '#0877aa',
      accent: 'MEASURES SYMMETRY',
    },
    {
      id: 'proto-2',
      event: 'SPRINT MECHANICS',
      name: 'ACCELERATION SPRINT',
      venue: 'RUNNING TRACK / TREADMILL',
      duration: '30 SECONDS',
      status: 'HIGH INTENSITY',
      statusColor: '#07171c',
      accent: 'GROUND REACTION FORCE',
    },
    {
      id: 'proto-3',
      event: 'NEURO-MUSCULAR',
      name: 'CADENCE DRILL (180+ SPM)',
      venue: 'SPEEDWAY CAPTURE ZONE',
      duration: '60 SECONDS',
      status: 'ELITE ATHLETES',
      statusColor: '#0877aa',
      accent: 'OSCILLATION & STRIDE',
    },
    {
      id: 'proto-4',
      event: 'POSTURAL STABILITY',
      name: 'SINGLE-LEG BALANCE TEST',
      venue: 'STATIC MARKER MAT',
      duration: '30 SECONDS',
      status: 'REHABILITATION',
      statusColor: '#07171c',
      accent: 'CENTER OF GRAVITY SWAY',
    },
  ];

  const benchmarks = [
    { rank: '01', athlete: 'MARCUS VANCE', discipline: '100m Sprint', score: '37.4 km/h', symmetry: '99.2%', confidence: '99.8%' },
    { rank: '02', athlete: 'ELENA ROSTOVA', discipline: '400m Hurdles', score: '31.8 km/h', symmetry: '99.0%', confidence: '99.6%' },
    { rank: '03', athlete: 'DEVON CHASE', discipline: 'Basketball Guard', score: '30.2 km/h', symmetry: '98.5%', confidence: '99.4%' },
    { rank: '04', athlete: 'LEO SANTOS', discipline: 'Football Forward', score: '34.2 km/h', symmetry: '98.1%', confidence: '99.2%' },
    { rank: '05', athlete: 'PRIYA NAIR', discipline: 'Fast Bowling Run-up', score: '28.6 km/h', symmetry: '98.4%', confidence: '99.5%' },
  ];
</script>

<div class="protocols-container" id="protocols-section">
  <div class="lb-header">
    <div>
      <span class="eyebrow">ATHLETE TESTING SUITE</span>
      <h3 class="title">GAIT PROTOCOLS & BENCHMARKS</h3>
    </div>
    <div class="lb-toggle">
      <button
        class:active={activeTab === 'protocols'}
        onclick={() => { activeTab = 'protocols'; }}
      >
        <span>⚡ TEST PROTOCOLS (4)</span>
      </button>
      <button
        class:active={activeTab === 'benchmarks'}
        onclick={() => { activeTab = 'benchmarks'; }}
      >
        <span>🏆 ATHLETE BENCHMARKS</span>
      </button>
    </div>
  </div>

  {#if activeTab === 'protocols'}
    <!-- Horizontal Protocols Track -->
    <div class="protocols-scroll-track" role="region" aria-label="Gait Protocols Track">
      {#each protocols as p}
        <div
          class="protocol-card"
          role="button"
          tabindex="0"
          onclick={onSelectProtocol}
          onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') onSelectProtocol(); }}
        >
          <div class="fix-top">
            <span class="fix-event">{p.event}</span>
            <span class="fix-status" style:color={p.statusColor}>
              {p.status}
            </span>
          </div>

          <h4 class="fix-teams">{p.name}</h4>

          <div class="fix-meta">
            <span>📍 {p.venue}</span>
            <span>⏱️ {p.duration}</span>
          </div>

          <div class="fix-foot">
            <span class="fix-accent">{p.accent}</span>
            <span class="fix-arrow">START TEST →</span>
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <!-- Benchmarks Table -->
    <div class="table-card">
      <table class="lb-table">
        <thead>
          <tr>
            <th>RANK</th>
            <th>ATHLETE</th>
            <th>DISCIPLINE</th>
            <th>PEAK VELOCITY</th>
            <th>BILATERAL SYMMETRY</th>
            <th>AI CONFIDENCE</th>
          </tr>
        </thead>
        <tbody>
          {#each benchmarks as b}
            <tr class:top-rank={b.rank === '01'}>
              <td class="r-num">#{b.rank}</td>
              <td class="r-name"><strong>{b.athlete}</strong></td>
              <td class="r-sport">{b.discipline}</td>
              <td class="r-score"><strong>{b.score}</strong></td>
              <td class="r-sym">{b.symmetry}</td>
              <td class="r-conf">{b.confidence}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .protocols-container {
    padding: 24px 0;
  }

  .lb-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: 20px;
    margin-bottom: 28px;
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

  .lb-toggle {
    display: flex;
    gap: 6px;
    background: #ffffff;
    padding: 4px;
    border-radius: 9999px;
    border: 1px solid #dce4e6;
  }

  .lb-toggle button {
    background: transparent;
    border: none;
    color: #607075;
    padding: 8px 18px;
    border-radius: 9999px;
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 12px;
    letter-spacing: 0.06em;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .lb-toggle button.active {
    background: #07171c;
    color: #ffffff;
  }

  /* Horizontal Scroll Track */
  .protocols-scroll-track {
    display: flex;
    gap: 20px;
    overflow-x: auto;
    padding: 6px 2px 20px;
    scroll-snap-type: x mandatory;
    scrollbar-width: thin;
    scrollbar-color: #00c8f5 #f1f5f7;
  }

  .protocols-scroll-track::-webkit-scrollbar {
    height: 6px;
  }

  .protocols-scroll-track::-webkit-scrollbar-thumb {
    background: #00c8f5;
    border-radius: 9999px;
  }

  .protocol-card {
    flex: 0 0 clamp(280px, 32vw, 360px);
    scroll-snap-align: start;
    background: #ffffff;
    border: 1px solid #e1e7e9;
    border-radius: 10px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 220px;
    box-shadow: 0 8px 24px rgba(7, 23, 28, 0.04);
    cursor: pointer;
    transition: transform 0.22s cubic-bezier(0.22, 1, 0.36, 1), border-color 0.22s ease, box-shadow 0.22s ease;
  }

  .protocol-card:hover {
    transform: translateY(-4px);
    border-color: #00c8f5;
    box-shadow: 0 14px 36px rgba(0, 200, 245, 0.12);
  }

  .fix-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .fix-event {
    font-family: 'Oswald', sans-serif;
    font-size: 10px;
    letter-spacing: 0.1em;
    color: #607075;
    font-weight: 700;
  }

  .fix-status {
    font-family: 'Oswald', sans-serif;
    font-size: 9px;
    letter-spacing: 0.12em;
    background: #f1f5f7;
    padding: 3px 8px;
    border-radius: 9999px;
    font-weight: 700;
  }

  .fix-teams {
    margin: 0 0 16px;
    font-family: 'Manrope', 'Anton', sans-serif;
    font-size: 21px;
    font-weight: 800;
    color: #07171c;
    letter-spacing: -0.02em;
    line-height: 1.2;
  }

  .fix-meta {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 13px;
    color: #607075;
    margin-bottom: 18px;
  }

  .fix-foot {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid #eef3f5;
    padding-top: 14px;
  }

  .fix-accent {
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    color: #0877aa;
    letter-spacing: 0.06em;
    font-weight: 700;
  }

  .fix-arrow {
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    color: #07171c;
    font-size: 12px;
    letter-spacing: 0.04em;
    transition: color 0.2s ease, transform 0.2s ease;
  }

  .protocol-card:hover .fix-arrow {
    color: #00c8f5;
    transform: translateX(4px);
  }

  /* Benchmarks Table */
  .table-card {
    background: #ffffff;
    border: 1px solid #e1e7e9;
    border-radius: 10px;
    overflow-x: auto;
    box-shadow: 0 8px 24px rgba(7, 23, 28, 0.04);
  }

  .lb-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    font-size: 14px;
  }

  .lb-table th {
    background: #f8f8f6;
    padding: 14px 20px;
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    letter-spacing: 0.1em;
    color: #607075;
    border-bottom: 1px solid #e1e7e9;
  }

  .lb-table td {
    padding: 16px 20px;
    border-bottom: 1px solid #f1f5f7;
    color: #07171c;
  }

  .lb-table tr:hover td {
    background: #f8fcfe;
  }

  .top-rank td {
    background: #f0fbff;
  }

  .r-num {
    font-family: 'Anton', sans-serif;
    font-size: 18px;
    color: #07171c;
  }

  .r-name strong {
    font-size: 14px;
    font-weight: 800;
  }

  .r-sport {
    color: #607075;
    font-size: 13px;
  }

  .r-score strong {
    font-family: 'Anton', sans-serif;
    font-size: 16px;
    color: #07171c;
  }

  .r-sym {
    font-family: 'Anton', sans-serif;
    color: #0098be;
  }

  .r-conf {
    font-family: 'Oswald', sans-serif;
    font-size: 12px;
    color: #607075;
  }
</style>
