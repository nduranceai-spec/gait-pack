<script lang="ts">
  import { onMount, tick } from 'svelte';
  import AppHeader from './components/AppHeader.svelte';
  import AppSidebar from './components/AppSidebar.svelte';
  import Coach from './pages/Coach.svelte';
  import Dashboard from './pages/Dashboard.svelte';
  import History from './pages/History.svelte';
  import Report from './pages/Report.svelte';
  import TestStudio from './pages/TestStudio.svelte';
  import { fetchSessions } from './lib/sessions';
  import type { PageId, Session } from './lib/types';

  let activePage = $state<PageId>('dashboard');
  let autoStart = $state(false);
  let sessions = $state<Session[]>([]);
  let loading = $state(true);
  let sessionError = $state('');
  let selectedSession = $state<Session | null>(null);
  let requestSequence = 0;
  const labels = {
    dashboard: ['Your movement, understood', 'Movement workspace'],
    studio: ['Capture with confidence', 'Test studio'],
    report: ['From capture to clarity', 'Session report'],
    history: ['Your movement library', 'Session history'],
    coach: ['A little clarity goes a long way', 'Help & guidance'],
  } as const;

  async function refreshSessions() {
    const sequence = ++requestSequence;
    loading = true;
    sessionError = '';
    try {
      const result = await fetchSessions(AbortSignal.timeout(8000));
      if (sequence === requestSequence) sessions = result;
      return result;
    } catch (error) {
      if (sequence === requestSequence) sessionError = error instanceof Error ? error.message : 'Cannot load recordings.';
      return [];
    } finally {
      if (sequence === requestSequence) loading = false;
    }
  }
  function navigate(page: PageId) {
    const changed = activePage !== page;
    autoStart = false;
    activePage = page;
    if (changed) void focusPage();
    if (page !== 'studio') void refreshSessions();
  }
  async function focusPage() {
    await tick();
    window.scrollTo({ top: 0, behavior: 'instant' });
    document.getElementById('page-title')?.focus({ preventScroll: true });
  }
  function openReport(session: Session) {
    selectedSession = session;
    navigate('report');
  }
  async function openSaved(file: string) {
    const result = await refreshSessions();
    selectedSession = result.find((session) => session.file === file) ?? null;
    activePage = 'report';
    void focusPage();
  }
  onMount(() => { void refreshSessions(); });
</script>

<div class="app-shell experience">
  <div class="ambient ambient-one"></div><div class="ambient ambient-two"></div>
  <AppSidebar active={activePage} onNavigate={navigate} />
  <main>
    <AppHeader eyebrow={labels[activePage][0]} title={labels[activePage][1]} onHelp={() => navigate('coach')} />
    {#key activePage}
      <div class="page-wrap">
        {#if activePage === 'dashboard'}
          <Dashboard {sessions} {loading} error={sessionError} onRetry={refreshSessions} onStart={() => navigate('studio')} onHistory={() => navigate('history')} onOpen={openReport} />
        {:else if activePage === 'studio'}
          <TestStudio {autoStart} onSaved={refreshSessions} onReport={openSaved} />
        {:else if activePage === 'history'}
          <History {sessions} {loading} error={sessionError} onRetry={refreshSessions} onOpen={openReport} onStart={() => navigate('studio')} />
        {:else if activePage === 'report'}
          <Report session={selectedSession ?? sessions[0] ?? null} {loading} error={sessionError} onHistory={() => navigate('history')} onStart={() => navigate('studio')} />
        {:else}
          <Coach onStart={() => navigate('studio')} />
        {/if}
      </div>
    {/key}
  </main>
</div>
