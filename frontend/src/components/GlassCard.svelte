<script lang="ts">
  import type { Snippet } from 'svelte';

  let {
    children,
    class: className = '',
    elevated = false,
  }: { children: Snippet; class?: string; elevated?: boolean } = $props();

  function reflection(element: HTMLElement) {
    const preference = window.matchMedia('(hover: hover) and (prefers-reduced-motion: no-preference)');
    let frame = 0;
    function move(event: PointerEvent) {
      if (!preference.matches) return;
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const bounds = element.getBoundingClientRect();
        element.style.setProperty('--reflection-x', `${event.clientX - bounds.left}px`);
        element.style.setProperty('--reflection-y', `${event.clientY - bounds.top}px`);
      });
    }
    element.addEventListener('pointermove', move);
    return {
      destroy() {
        cancelAnimationFrame(frame);
        element.removeEventListener('pointermove', move);
      },
    };
  }
</script>

<section use:reflection class:glass-elevated={elevated} class="glass-card {className}">
  {@render children()}
</section>
