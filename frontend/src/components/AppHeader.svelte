<script lang="ts">
  import { CircleHelp, ShieldCheck } from '@lucide/svelte';
  let { title, eyebrow, onHelp }: { title: string; eyebrow: string; onHelp: () => void } = $props();
</script>

<header class="app-header">
  <div><p class="eyebrow">{eyebrow}</p><h1 id="page-title" tabindex="-1">{title}</h1></div>
  <div class="header-actions">
    <span class="workspace-badge"><ShieldCheck size={15} /> Local workspace</span>
    <button class="icon-button" aria-label="Open help and guidance" onclick={onHelp}><CircleHelp size={20} /></button>
  </div>
</header>
