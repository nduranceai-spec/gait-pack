<script lang="ts">
  import { createSession } from './lib/api';
  import { activityType, sessionId, testDuration } from './lib/stores/session';
  import { personProfile, validatePersonProfile } from './lib/stores/person';
  import GaitTest from './routes/gait-test/+page.svelte';
  import Activity from './routes/activity/+page.svelte';
  import Result from './routes/result/[sessionId]/+page.svelte';

  type Stage = 'start' | 'camera' | 'activity' | 'result';
  let stage = $state<Stage>('start');
  let completedSessionId = $state<string | null>(null);
  let starting = $state(false);
  let error = $state('');

  async function startTest() {
    if (starting) return;
    starting = true;
    error = '';
    try {
      validatePersonProfile();
      const session = await createSession();
      sessionId.set(session.sessionId);
      activityType.set('Normal Walk');
      completedSessionId = null;
      stage = 'camera';
    } catch (failure) {
      error = failure instanceof Error ? failure.message : 'GAIT could not start a test. Check that the local backend is running.';
    } finally {
      starting = false;
    }
  }

  function reset() {
    completedSessionId = null;
    sessionId.clear();
    stage = 'start';
  }

</script>

<svelte:head>
  <title>GAIT — Live movement test</title>
  <meta name="description" content="A focused live gait test with movement detection and an instant report." />
</svelte:head>

{#if stage === 'camera'}
  <GaitTest onExit={reset} onActivity={() => stage = 'activity'} />
{:else if stage === 'activity'}
  <Activity onExit={() => stage = 'camera'} onComplete={(id) => { completedSessionId = id; stage = 'result'; }} />
{:else if stage === 'result' && completedSessionId}
  <Result sessionId={completedSessionId} onRetake={startTest} onExit={reset} />
{:else}
  <main class="start-shell">
    <section class="start-card" aria-labelledby="start-title">
      <p class="eyebrow"><i></i> NEW MOVEMENT TEST</p>
      <span class="step">01 / 03 · PERSON DETAILS</span>
      <h1 id="start-title">Build your<br /><em>baseline.</em></h1>
      <p class="summary">Add the participant details, choose a capture length, then prepare the cameras.</p>
      <form class="person-form" onsubmit={(event) => { event.preventDefault(); void startTest(); }}>
        <label class="wide"><span>Participant name</span><input bind:value={$personProfile.name} autocomplete="name" placeholder="Full name" required /></label>
        <label><span>Age</span><input bind:value={$personProfile.age} type="number" min="1" max="120" inputmode="numeric" placeholder="Years" required /></label>
        <label><span>Height</span><input bind:value={$personProfile.height} type="number" min="50" max="260" inputmode="decimal" placeholder="cm" required /></label>
        <label><span>Weight</span><input bind:value={$personProfile.weight} type="number" min="10" max="400" inputmode="decimal" placeholder="kg" required /></label>
        <fieldset class="duration-picker"><legend>Capture duration</legend><div>{#each [30, 60, 120] as duration}<button type="button" class:active={$testDuration === duration} onclick={() => testDuration.set(duration as 30 | 60 | 120)}>{duration < 60 ? '30 SEC' : duration === 60 ? '1 MIN' : '2 MIN'}</button>{/each}</div></fieldset>
        <button class="start-button" type="submit" disabled={starting}>{starting ? 'STARTING…' : 'CONTINUE TO CAMERAS'} <span>→</span></button>
      </form>
      <p class="privacy">The profile, camera recordings, and final analysis are saved locally on this laptop.</p>
      {#if error}<p class="start-error" role="alert">{error}</p>{/if}
    </section>
    <aside class="flow" aria-label="Test flow"><span class="active">Start</span><i></i><span>Live detection</span><i></i><span>Result</span></aside>
  </main>
{/if}

<style>
  .start-shell{min-height:100svh;display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:end;gap:40px;padding:clamp(24px,4vw,62px);background:var(--paper);color:var(--ink)}
  .start-card{max-width:760px;padding-bottom:clamp(50px,8vh,100px)}
  .eyebrow{display:flex;align-items:center;gap:8px;margin:0 0 32px;color:var(--muted);font-size:10px;font-weight:800;letter-spacing:.11em}.eyebrow i{width:7px;height:7px;border-radius:50%;background:var(--cyan);box-shadow:0 0 0 5px #00c8f520}
  .step{display:block;margin-bottom:20px;color:var(--muted);font-size:11px;font-weight:800;letter-spacing:.08em}
  h1{margin:0;font-size:clamp(76px,12vw,176px);line-height:.76;letter-spacing:-.115em}h1 em{font-style:normal;color:var(--cyan)}
  .summary{max-width:500px;margin:34px 0 25px;color:var(--muted);font-size:clamp(16px,1.7vw,21px);line-height:1.45;letter-spacing:-.025em}
  .person-form{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;max-width:680px}.person-form label{display:grid;gap:7px;color:var(--muted);font-size:10px;font-weight:800;letter-spacing:.06em}.person-form label.wide,.duration-picker,.person-form>.start-button{grid-column:1/-1}.person-form input{width:100%;border:1px solid #aebbbc;background:#fff;color:var(--ink);padding:13px 12px;outline:0;font:600 14px/1 inherit}.person-form input:focus{border-color:var(--ink);box-shadow:0 0 0 3px #00c8f52b}.duration-picker{margin:8px 0 3px;padding:0;border:0}.duration-picker legend{margin-bottom:9px;color:var(--muted);font-size:10px;font-weight:800;letter-spacing:.06em}.duration-picker div{display:flex;gap:6px}.duration-picker button{border:1px solid #aebbbc;background:transparent;padding:10px 14px;color:var(--ink);font-size:10px;font-weight:800;letter-spacing:.06em;cursor:pointer}.duration-picker button.active{border-color:var(--ink);background:var(--ink);color:var(--paper)}.person-form>.start-button{justify-content:space-between;max-width:280px;margin-top:6px}
  .start-button{display:inline-flex;align-items:center;gap:34px;border:0;background:var(--ink);color:var(--paper);padding:18px 20px 18px 23px;font:800 13px/1 inherit;letter-spacing:.07em;cursor:pointer}.start-button span{color:var(--cyan);font-size:23px;line-height:.5}.start-button:disabled{opacity:.5;cursor:wait}
  .privacy{max-width:360px;margin:20px 0 0;color:var(--muted);font-size:10px;line-height:1.55}.start-error{max-width:520px;margin:18px 0 0;padding:11px 13px;background:#ffe9e4;color:#852814;font-size:12px;font-weight:700}
  .flow{display:flex;align-items:center;gap:10px;padding-bottom:8px;color:var(--muted);font-size:10px;font-weight:800;letter-spacing:.07em;white-space:nowrap}.flow .active{color:var(--ink)}.flow i{width:28px;height:1px;background:#aebbbc}
  @media(max-width:680px){.start-shell{grid-template-columns:1fr;padding:24px;align-content:space-between;gap:32px}.start-card{padding:70px 0 0}.flow{order:-1;align-self:start}.flow i{width:15px}h1{font-size:clamp(70px,20vw,118px)}.summary{margin-top:30px}.person-form{grid-template-columns:1fr 1fr}.person-form .wide,.duration-picker,.person-form>.start-button{grid-column:1/-1}}
  @media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
</style>
