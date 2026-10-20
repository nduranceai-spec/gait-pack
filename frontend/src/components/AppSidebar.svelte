<script lang="ts">
  import {
    Activity,
    BrainCircuit,
    ChartNoAxesCombined,
    LayoutDashboard,
    History,
    Sparkles,
  } from '@lucide/svelte';
  import type { PageId } from '../lib/types';

  let {
    active,
    onNavigate,
  }: { active: PageId; onNavigate: (page: PageId) => void } = $props();

  const items = [
    { id: 'dashboard' as const, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'studio' as const, label: 'Test Studio', icon: Activity },
    { id: 'report' as const, label: 'Gait Report', icon: ChartNoAxesCombined },
    { id: 'history' as const, label: 'Session History', icon: History },
    { id: 'coach' as const, label: 'Help & Guidance', icon: BrainCircuit },
  ];
</script>

<aside class="sidebar" aria-label="Main navigation">
  <div class="brand-lockup">
    <div class="brand-mark"><Sparkles size={20} strokeWidth={1.8} /></div>
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
