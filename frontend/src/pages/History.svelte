<script lang="ts">
  import { ArrowRight, RefreshCw, Search, FolderOpen } from '@lucide/svelte';
  import GlassCard from '../components/GlassCard.svelte';
  import SessionList from '../components/SessionList.svelte';
  import type { Session } from '../lib/types';
  let { sessions, loading, error, onRetry, onOpen, onStart }: {
    sessions: Session[]; loading: boolean; error: string; onRetry: () => void;
    onOpen: (session: Session) => void; onStart: () => void;
  } = $props();
  let query = $state('');
  let filter = $state('all');
  let visible = $derived(sessions.filter((session) =>
    (filter === 'all' || session.status === filter) &&
    `${session.name} ${session.activity} ${session.file}`.toLowerCase().includes(query.toLowerCase())
  ));
</script>

<div class="page-stack">
  <div class="page-intro"><div><p class="eyebrow">A record of your movement</p><h2>Every session.<br /><em>In one place.</em></h2><p>Browse the recordings saved on this device. Open a session to inspect its capture details.</p></div><button class="primary-button" onclick={onStart}>New recording <ArrowRight size={18} /></button></div>
  <GlassCard>
    <div class="library-toolbar">
      <label class="search-control"><Search size={18} /><span class="sr-only">Search recordings</span><input type="search" placeholder="Search recordings…" bind:value={query} /></label>
      <label class="filter-control"><span class="sr-only">Filter by recording status</span><select bind:value={filter}><option value="all">All recordings</option><option value="saved">With pose data</option><option value="empty">No pose data</option><option value="unreadable">Unreadable</option></select></label>
      <button class="icon-button" aria-label="Refresh recordings" disabled={loading} onclick={onRetry}><RefreshCw size={18} /></button>
    </div>
    <div class="library-count"><span>{loading ? 'Loading library…' : `${visible.length} recordings`}</span><span>NEWEST FIRST · LOCAL CSV</span></div>
    {#if loading}<p class="quiet-message" role="status">Reading your saved sessions…</p>
    {:else if error}<p class="inline-notice" role="alert">{error}</p>
    {:else if visible.length}<SessionList sessions={visible} {onOpen} />
    {:else}<div class="empty-library"><FolderOpen size={34} /><h3>{sessions.length ? 'No matching recordings' : 'Your library is ready'}</h3><p>{sessions.length ? 'Try another name or choose a different filter.' : 'Complete your first capture to see its details here.'}</p>{#if sessions.length}<button class="text-button" onclick={() => { query = ''; filter = 'all'; }}>Clear filters</button>{:else}<button class="text-button" onclick={onStart}>Begin a gait test <ArrowRight size={16} /></button>{/if}</div>{/if}
  </GlassCard>
  <p class="section-note">Sample span is the interval between the first and last recorded pose. A saved file does not necessarily contain a full 60-second test.</p>
</div>
