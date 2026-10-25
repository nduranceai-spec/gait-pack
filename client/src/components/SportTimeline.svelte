<script lang="ts">
  interface Milestone {
    time: string;
    stage: string;
    headline: string;
    metric: string;
    metricLabel: string;
    detail: string;
    tag: string;
    tagColor: string;
  }

  let milestones: Milestone[] = [
    {
      time: '00:00',
      stage: 'INITIAL CONTACT',
      headline: 'FOOT STRIKE & GROUND IMPACT',
      metric: '182 ms',
      metricLabel: 'CONTACT TIME',
      detail: 'Ankle dorsiflexion aligned at 8°. Ground reaction force smoothly channeled through calcaneus into midfoot transition.',
      tag: 'STRIKE ZONE',
      tagColor: '#00c8f5',
    },
    {
      time: '00:15',
      stage: 'LOADING RESPONSE',
      headline: 'KNEE EXTENSION & SHOCK ATTENUATION',
      metric: '18.4°',
      metricLabel: 'KNEE FLEXION ANGLE',
      detail: 'Quadriceps eccentrically load to dampen vertical impact. MediaPipe confirms 0.4° frontal knee valgus balance.',
      tag: 'SHOCK ABSORPTION',
      tagColor: '#07171c',
    },
    {
      time: '00:30',
      stage: 'MID-STANCE DRIVE',
      headline: 'TERMINAL PROPULSION VELOCITY',
      metric: '192 SPM',
      metricLabel: 'PEAK CADENCE',
      detail: 'Center of mass cleanly passes directly over the supportive foot. Pelvic tilt remains stable within 2.2° of baseline.',
      tag: 'CENTER OF MASS',
      tagColor: '#00c8f5',
    },
    {
      time: '00:45',
      stage: 'TERMINAL TOE-OFF',
      headline: 'EXPLOSIVE PLANTAR FLEXION',
      metric: '3.8 BW',
      metricLabel: 'PROPULSION FORCE',
      detail: 'Great toe extension achieves 62° at push-off, producing maximum horizontal propulsion with minimal braking friction.',
      tag: 'PUSH-OFF DRIVE',
      tagColor: '#07171c',
    },
    {
      time: '01:00',
      stage: 'SWING & RECOVERY',
      headline: 'BILATERAL GAIT SYMMETRY',
      metric: '98.8%',
      metricLabel: 'SYMMETRY INDEX',
      detail: 'Complete bilateral gait cycle computed across left and right lower extremities with sub-millimeter precision.',
      tag: 'CYCLE COMPLETE',
      tagColor: '#00c8f5',
    },
  ];

  let activeIndex = $state(2);
  let current = $derived(milestones[activeIndex]);
</script>

<div class="timeline-container">
  <div class="timeline-head">
    <div>
      <span class="eyebrow">KINEMATIC STRIDE PROGRESSION</span>
      <h3 class="title">GAIT TEST PHASE TIMELINE</h3>
    </div>
    <div class="timeline-tabs">
      {#each milestones as m, i}
        <button
          class="time-tab"
          class:active={activeIndex === i}
          onclick={() => { activeIndex = i; }}
        >
          <span>{m.time}</span>
        </button>
      {/each}
    </div>
  </div>

  <!-- Timeline Track -->
  <div class="timeline-track">
    <div
      class="track-progress-fill"
      style:width={`${(activeIndex / (milestones.length - 1)) * 100}%`}
    ></div>

    <div class="nodes-row">
      {#each milestones as m, i}
        <button
          class="timeline-node"
          class:active={activeIndex === i}
          class:passed={activeIndex >= i}
          onclick={() => { activeIndex = i; }}
          aria-label={m.stage}
        >
          <span class="node-dot"></span>
          <span class="node-time">{m.time}</span>
          <span class="node-stage">{m.stage}</span>
        </button>
      {/each}
    </div>
  </div>

  <!-- Active Milestone Showcase -->
  <div class="milestone-display">
    <div class="display-left">
      <div class="tag-row">
        <span class="m-tag">{current.tag}</span>
        <span class="m-time-pill">{current.time} SECONDS</span>
      </div>
      <h4 class="m-headline">{current.headline}</h4>
      <p class="m-detail">{current.detail}</p>
    </div>

    <div class="display-right">
      <div class="metric-box">
        <span class="met-label">{current.metricLabel}</span>
        <strong class="met-value">{current.metric}</strong>
        <span class="met-source">33-POINT AI EXTRACTION</span>
      </div>
    </div>
  </div>
</div>

<style>
  .timeline-container {
    background: #ffffff;
    border: 1px solid #e1e7e9;
    border-radius: 12px;
    padding: clamp(24px, 4vw, 44px);
    margin: 24px 0;
    box-shadow: 0 8px 30px rgba(7, 23, 28, 0.04);
  }

  .timeline-head {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: 20px;
    margin-bottom: 36px;
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

  .timeline-tabs {
    display: flex;
    gap: 6px;
    background: #f1f5f7;
    padding: 4px;
    border-radius: 6px;
  }

  .time-tab {
    background: transparent;
    border: none;
    color: #607075;
    padding: 6px 14px;
    font-family: 'Anton', sans-serif;
    font-size: 13px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .time-tab.active {
    background: #07171c;
    color: #ffffff;
  }

  /* Timeline Track */
  .timeline-track {
    position: relative;
    padding: 24px 0 36px;
    margin-bottom: 24px;
  }

  .timeline-track::before {
    content: '';
    position: absolute;
    top: 32px;
    left: 0;
    right: 0;
    height: 3px;
    background: #e1e7e9;
  }

  .track-progress-fill {
    position: absolute;
    top: 32px;
    left: 0;
    height: 3px;
    background: #00c8f5;
    transition: width 0.4s cubic-bezier(0.22, 1, 0.36, 1);
    box-shadow: 0 0 10px rgba(0, 200, 245, 0.5);
    z-index: 1;
  }

  .nodes-row {
    position: relative;
    display: flex;
    justify-content: space-between;
    z-index: 2;
  }

  .timeline-node {
    background: transparent;
    border: none;
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: pointer;
    padding: 0;
  }

  .node-dot {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #ffffff;
    border: 3px solid #b5c7cb;
    margin-bottom: 12px;
    transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .timeline-node.passed .node-dot {
    border-color: #07171c;
    background: #07171c;
  }

  .timeline-node.active .node-dot {
    border-color: #00c8f5;
    background: #00c8f5;
    transform: scale(1.35);
    box-shadow: 0 0 14px rgba(0, 200, 245, 0.6);
  }

  .node-time {
    font-family: 'Anton', sans-serif;
    font-size: 15px;
    color: #07171c;
    margin-bottom: 2px;
  }

  .node-stage {
    font-family: 'Oswald', sans-serif;
    font-size: 10px;
    letter-spacing: 0.08em;
    color: #607075;
  }

  .timeline-node.active .node-stage {
    color: #0877aa;
    font-weight: 700;
  }

  /* Active Milestone Showcase */
  .milestone-display {
    background: #f8f8f6;
    border: 1px solid #e1e7e9;
    border-radius: 8px;
    padding: 26px;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 28px;
    align-items: center;
    animation: fadeIn 0.3s cubic-bezier(0.22, 1, 0.36, 1);
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .tag-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
  }

  .m-tag {
    font-family: 'Oswald', sans-serif;
    font-size: 10px;
    letter-spacing: 0.1em;
    padding: 3px 9px;
    border-radius: 9999px;
    background: #dff8ff;
    color: #0877aa;
    font-weight: 700;
  }

  .m-time-pill {
    font-family: 'Anton', sans-serif;
    font-size: 12px;
    color: #607075;
    letter-spacing: 0.06em;
  }

  .m-headline {
    margin: 0 0 8px;
    font-family: 'Manrope', 'Anton', sans-serif;
    font-size: clamp(20px, 3vw, 30px);
    font-weight: 800;
    color: #07171c;
    letter-spacing: -0.02em;
  }

  .m-detail {
    margin: 0;
    color: #607075;
    font-size: 15px;
    line-height: 1.5;
    max-width: 580px;
  }

  .metric-box {
    background: #ffffff;
    border: 1px solid #dce4e6;
    border-radius: 8px;
    padding: 20px 26px;
    text-align: right;
    min-width: 190px;
    box-shadow: 0 4px 14px rgba(7, 23, 28, 0.04);
  }

  .met-label {
    display: block;
    font-family: 'Oswald', sans-serif;
    font-size: 10px;
    letter-spacing: 0.1em;
    color: #607075;
    margin-bottom: 4px;
    font-weight: 700;
  }

  .met-value {
    display: block;
    font-family: 'Anton', sans-serif;
    font-size: 40px;
    line-height: 0.95;
    letter-spacing: -0.02em;
    color: #07171c;
    margin-bottom: 4px;
  }

  .met-source {
    font-family: 'Oswald', sans-serif;
    font-size: 9px;
    color: #8c9ea4;
    letter-spacing: 0.08em;
  }

  @media (max-width: 768px) {
    .milestone-display {
      grid-template-columns: 1fr;
    }
    .metric-box {
      text-align: left;
    }
    .node-stage {
      display: none;
    }
  }
</style>
