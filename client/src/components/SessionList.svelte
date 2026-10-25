<script lang="ts">
  import { ArrowUpRight, Footprints } from '@lucide/svelte';
  import type { Session } from '../lib/types';
  import { sessionDate, sessionDuration } from '../lib/sessions';
  import StatusPill from './StatusPill.svelte';
  let { sessions, onOpen }: { sessions: Session[]; onOpen: (session: Session) => void } = $props();
</script>

<div class="recording-list">
  {#each sessions as session (session.sessionId ?? session.file)}
    <article class="recording-row">
      <div class="session-icon"><Footprints size={19} /></div>
      <div class="recording-title"><strong>{session.name.replaceAll('-', ' ')}</strong><small>{sessionDate(session.date)}</small></div>
      <div class="recording-measure"><strong>{sessionDuration(session.sample_span_ms)}</strong><small>sample span</small></div>
      <StatusPill label={session.status === 'saved' ? 'Saved' : session.status === 'empty' ? 'No pose data' : 'Unreadable'} />
      <button class="round-action" aria-label={`Open recording ${session.name}`} onclick={() => onOpen(session)}><ArrowUpRight size={19} /></button>
    </article>
  {/each}
</div>
