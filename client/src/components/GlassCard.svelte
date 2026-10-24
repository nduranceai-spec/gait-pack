<script lang="ts">
  import type { Snippet } from 'svelte';

  let {
    children,
    class: className = '',
    elevated = false,
  }: { children: Snippet; class?: string; elevated?: boolean } = $props();

</script>

<section class:glass-elevated={elevated} class="glass-card {className}">
  {@render children()}
</section>
