<script lang="ts">
  import {
    Activity,
    BrainCircuit,
    ChartNoAxesCombined,
    LayoutDashboard,
    History,
    Footprints,
  } from '@lucide/svelte';
  import type { PageId } from '../lib/types';

  let {
    active,
    onNavigate,
  }: { active: PageId; onNavigate: (page: PageId) => void } = $props();

  const items = [
    { id: 'dashboard' as const, label: 'Overview', icon: LayoutDashboard },
    { id: 'studio' as const, label: 'Test studio', icon: Activity },
    { id: 'report' as const, label: 'Report', icon: ChartNoAxesCombined },
    { id: 'history' as const, label: 'Recordings', icon: History },
    { id: 'coach' as const, label: 'Guidance', icon: BrainCircuit },
  ];
</script>

<aside class="sidebar" aria-label="Main navigation">
  <div class="brand-lockup">
    <div class="brand-mark"><Footprints size={30} strokeWidth={1.6} /></div>
    <div>
      <strong>AURA</strong>
      <span>MOTION</span>
    </div>
  </div>

  <nav>
    {#each items as item}
      <button
        class:active={active === item.id}
        onclick={() => onNavigate(item.id)}
        aria-current={active === item.id ? 'page' : undefined}
        aria-label={item.label}
        title={item.label}
      >
        <item.icon size={20} strokeWidth={1.7} />
        <span>{item.label}</span>
      </button>
    {/each}
  </nav>

  <div class="sidebar-foot">
    <span class="local-dot"></span>
    <div><strong>Local-first</strong><small>Private by design</small></div>
  </div>
</aside>
