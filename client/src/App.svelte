<script lang="ts">
  import { onMount } from 'svelte';
  import { createSession } from './lib/api';
  import { fetchSessions } from './lib/sessions';
  import { activityType, captureViews, sessionId, testDuration } from './lib/stores/session';
  import { personProfile, validatePersonProfile } from './lib/stores/person';
  import type { PageId, Session } from './lib/types';
  import AppHeader from './components/AppHeader.svelte';
  import AppSidebar from './components/AppSidebar.svelte';
  import Activity from './routes/activity/+page.svelte';
  import GaitTest from './routes/gait-test/+page.svelte';
  import Result from './routes/result/[sessionId]/+page.svelte';
  import Coach from './pages/Coach.svelte';
  import Dashboard from './pages/Dashboard.svelte';
  import History from './pages/History.svelte';
  import Report from './pages/Report.svelte';

  type Stage = 'workspace' | 'start' | 'camera' | 'activity' | 'result';
  type WorkspacePage = Exclude<PageId, 'studio'>;
  const pageInfo: Record<PageId, { eyebrow: string; title: string }> = {
    dashboard: { eyebrow: 'Movement workspace', title: 'Overview' },
    studio: { eyebrow: 'Guided capture', title: 'New movement test' },
    report: { eyebrow: 'Session detail', title: 'Recording report' },
    history: { eyebrow: 'Saved locally', title: 'Recordings' },
    coach: { eyebrow: 'Learn and prepare', title: 'Guidance' },
  };

  let stage = $state<Stage>('workspace');
  let activePage = $state<PageId>('dashboard');
  let completedSessionId = $state<string | null>(null);
  let selectedFile = $state('');
  let sessions = $state<Session[]>([]);
  let sessionsLoading = $state(true);
  let sessionsError = $state('');
  let starting = $state(false);
  let error = $state('');

  const selectedSession = $derived(sessions.find((item) => item.file === selectedFile) ?? null);

  async function refreshSessions() {
    sessionsLoading = true;
    sessionsError = '';
    try {
      sessions = await fetchSessions();
    } catch (failure) {
      sessionsError = failure instanceof Error ? failure.message : 'Saved sessions could not be loaded.';
    } finally {
      sessionsLoading = false;
    }
  }

  function locationFor(page: PageId): string {
    if (page === 'studio') return '/studio';
    return page === 'dashboard' ? '/' : `/${page}`;
  }

  function applyLocation() {
    const path = window.location.pathname.replace(/\/+$/, '') || '/';
    const query = new URLSearchParams(window.location.search);
    const resultMatch = path.match(/^\/result\/(gait-[0-9a-f]{32})$/);

    if (resultMatch) {
      completedSessionId = resultMatch[1];
      stage = 'result';
      activePage = 'studio';
      return;
    }

    switch (path) {
      case '/studio':
      case '/test':
        activePage = 'studio';
        stage = 'start';
        break;
      case '/gait-test':
      case '/camera':
        if ($sessionId) {
          activePage = 'studio';
          stage = 'camera';
        } else {
          activePage = 'studio';
          stage = 'start';
        }
        break;
      case '/activity': {
        let hasCaptureViews = false;
        const unsubscribe = captureViews.subscribe((views) => {
          hasCaptureViews = Object.keys(views).length > 0;
        });
        unsubscribe();
        activePage = 'studio';
        stage = hasCaptureViews ? 'activity' : 'start';
        break;
      }
      case '/history':
        activePage = 'history';
        stage = 'workspace';
        break;
      case '/coach':
        activePage = 'coach';
        stage = 'workspace';
        break;
      case '/report':
        activePage = 'report';
        stage = 'workspace';
        selectedFile = query.get('file') || '';
        break;
      case '/':
      case '/dashboard':
      default:
        activePage = 'dashboard';
        stage = 'workspace';
        break;
    }
  }

  function navigate(page: PageId, replace = false) {
    activePage = page;
    stage = page === 'studio' ? 'start' : 'workspace';
    selectedFile = '';
    error = '';
    const path = locationFor(page);
    if (replace) window.history.replaceState(null, '', path);
    else if (window.location.pathname !== path) window.history.pushState(null, '', path);
  }

  function openSession(item: Session) {
    if (item.sessionId) {
      completedSessionId = item.sessionId;
      stage = 'result';
      activePage = 'studio';
      window.history.pushState(null, '', `/result/${encodeURIComponent(item.sessionId)}`);
      return;
    }
    selectedFile = item.file;
    activePage = 'report';
    stage = 'workspace';
    const params = new URLSearchParams({ file: item.file });
    window.history.pushState(null, '', `/report?${params}`);
  }

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
      window.history.pushState(null, '', '/gait-test');
    } catch (failure) {
      error = failure instanceof Error ? failure.message : 'GAIT could not start a test. Check that the local backend is running.';
    } finally {
      starting = false;
    }
  }

  function reset() {
    completedSessionId = null;
    sessionId.clear();
    navigate('dashboard');
  }

  function showActivity() {
    stage = 'activity';
    window.history.pushState(null, '', '/activity');
  }

  function completeTest(id: string) {
    completedSessionId = id;
    stage = 'result';
    window.history.pushState(null, '', `/result/${encodeURIComponent(id)}`);
    void refreshSessions();
  }

  onMount(() => {
    applyLocation();
    void refreshSessions();
    const handlePopState = () => applyLocation();
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  });
</script>

<svelte:head>
  <title>GAIT — Movement workspace</title>
  <meta name="description" content="Capture movement, keep your recordings, and review gait analysis." />
</svelte:head>

{#if stage === 'camera'}
  <GaitTest onExit={reset} onActivity={showActivity} />
{:else if stage === 'activity'}
  <Activity onExit={() => { stage = 'camera'; window.history.pushState(null, '', '/gait-test'); }} onComplete={completeTest} />
{:else if stage === 'result' && completedSessionId}
  <Result
    sessionId={completedSessionId}
    onRetake={() => { completedSessionId = null; navigate('studio'); }}
    onExit={reset}
  />
{:else if stage === 'start'}
  <main class="start-shell">
    <button class="workspace-back" onclick={() => navigate('dashboard')}>← WORKSPACE</button>
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
{:else}
  <div class="app-shell experience">
    <AppSidebar active={activePage} onNavigate={navigate} />
    <main>
      <AppHeader
        eyebrow={pageInfo[activePage].eyebrow}
        title={pageInfo[activePage].title}
        onHelp={() => navigate('coach')}
      />
      <section class="page-wrap">
        {#if activePage === 'dashboard'}
          <Dashboard
            {sessions}
            loading={sessionsLoading}
            error={sessionsError}
            onRetry={refreshSessions}
            onStart={() => navigate('studio')}
            onHistory={() => navigate('history')}
            onOpen={openSession}
          />
        {:else if activePage === 'history'}
          <History
            {sessions}
            loading={sessionsLoading}
            error={sessionsError}
            onRetry={refreshSessions}
            onStart={() => navigate('studio')}
            onOpen={openSession}
          />
        {:else if activePage === 'report'}
          <Report
            session={selectedSession}
            loading={sessionsLoading}
            error={sessionsError}
            onHistory={() => navigate('history')}
            onStart={() => navigate('studio')}
          />
        {:else if activePage === 'coach'}
          <Coach onStart={() => navigate('studio')} />
        {/if}
      </section>
    </main>
  </div>
{/if}

<style>
  .start-shell{min-height:100svh;display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:end;gap:40px;padding:clamp(24px,4vw,62px);background:var(--paper);color:var(--ink)}
  .workspace-back{position:absolute;top:24px;left:clamp(24px,4vw,62px);border:0;background:none;color:var(--muted);font-size:10px;font-weight:800;letter-spacing:.08em}
  .start-card{max-width:760px;padding-bottom:clamp(50px,8vh,100px)}
  .eyebrow{display:flex;align-items:center;gap:8px;margin:0 0 32px;color:var(--muted);font-size:10px;font-weight:800;letter-spacing:.11em}.eyebrow i{width:7px;height:7px;border-radius:50%;background:var(--cyan);box-shadow:0 0 0 5px #00c8f520}
  .step{display:block;margin-bottom:20px;color:var(--muted);font-size:11px;font-weight:800;letter-spacing:.08em}
  h1{margin:0;font-size:clamp(76px,12vw,176px);line-height:.76;letter-spacing:-.115em}h1 em{font-style:normal;color:var(--cyan)}
  .summary{max-width:500px;margin:34px 0 25px;color:var(--muted);font-size:clamp(16px,1.7vw,21px);line-height:1.45;letter-spacing:-.025em}
  .person-form{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;max-width:680px}.person-form label{display:grid;gap:7px;color:var(--muted);font-size:10px;font-weight:800;letter-spacing:.06em}.person-form label.wide,.duration-picker,.person-form>.start-button{grid-column:1/-1}.person-form input{width:100%;border:1px solid #aebbbc;background:#fff;color:var(--ink);padding:13px 12px;outline:0;font:600 14px/1 inherit}.person-form input:focus{border-color:var(--ink);box-shadow:0 0 0 3px #00c8f52b}.duration-picker{margin:8px 0 3px;padding:0;border:0}.duration-picker legend{margin-bottom:9px;color:var(--muted);font-size:10px;font-weight:800;letter-spacing:.06em}.duration-picker div{display:flex;gap:6px}.duration-picker button{border:1px solid #aebbbc;background:transparent;padding:10px 14px;color:var(--ink);font-size:10px;font-weight:800;letter-spacing:.06em;cursor:pointer}.duration-picker button.active{border-color:var(--ink);background:var(--ink);color:var(--paper)}.person-form>.start-button{justify-content:space-between;max-width:280px;margin-top:6px}
  .start-button{display:inline-flex;align-items:center;gap:34px;border:0;background:var(--ink);color:var(--paper);padding:18px 20px 18px 23px;font:800 13px/1 inherit;letter-spacing:.07em;cursor:pointer}.start-button span{color:var(--cyan);font-size:23px;line-height:.5}.start-button:disabled{opacity:.5;cursor:wait}
  .privacy{max-width:360px;margin:20px 0 0;color:var(--muted);font-size:10px;line-height:1.55}.start-error{max-width:520px;margin:18px 0 0;padding:11px 13px;background:#ffe9e4;color:#852814;font-size:12px;font-weight:700}
  .flow{display:flex;align-items:center;gap:10px;padding-bottom:8px;color:var(--muted);font-size:10px;font-weight:800;letter-spacing:.07em;white-space:nowrap}.flow .active{color:var(--ink)}.flow i{width:28px;height:1px;background:#aebbbc}
  @media(max-width:680px){.start-shell{grid-template-columns:1fr;padding:24px;align-content:space-between;gap:32px}.workspace-back{top:14px;left:24px}.start-card{padding:70px 0 0}.flow{order:-1;align-self:start}.flow i{width:15px}h1{font-size:clamp(70px,20vw,118px)}.summary{margin-top:30px}.person-form{grid-template-columns:1fr 1fr}.person-form .wide,.duration-picker,.person-form>.start-button{grid-column:1/-1}}
  @media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
</style>
