<script lang="ts">
  export interface TabItem {
    id: string;
    label: string;
    meta?: string;
  }

  let {
    items,
    value,
    label,
    onChange,
    compact = false,
    disabled = false,
  }: {
    items: TabItem[];
    value: string;
    label: string;
    onChange: (id: string) => void;
    compact?: boolean;
    disabled?: boolean;
  } = $props();

  function onKeydown(event: KeyboardEvent) {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const current = items.findIndex((item) => item.id === value);
    const next = event.key === 'Home'
      ? 0
      : event.key === 'End'
        ? items.length - 1
        : (current + (event.key === 'ArrowRight' ? 1 : -1) + items.length) % items.length;
    onChange(items[next].id);
    requestAnimationFrame(() => {
      document.querySelector<HTMLButtonElement>(`[data-tab-id="${CSS.escape(items[next].id)}"]`)?.focus();
    });
  }
</script>

<div class:compact class="tabs" role="tablist" aria-label={label} tabindex="-1" onkeydown={onKeydown}>
  {#each items as item}
    <button
      type="button"
      role="tab"
      aria-selected={value === item.id}
      tabindex={value === item.id ? 0 : -1}
      data-tab-id={item.id}
      class:active={value === item.id}
      disabled={disabled}
      onclick={() => onChange(item.id)}
    >
      <span>{item.label}</span>
      {#if item.meta}<small>{item.meta}</small>{/if}
      <i aria-hidden="true"></i>
    </button>
  {/each}
</div>

<style>
  .tabs{display:flex;gap:4px;overflow-x:auto;scrollbar-width:none}.tabs::-webkit-scrollbar{display:none}.tabs button{position:relative;flex:0 0 auto;min-height:56px;padding:10px 14px;border:1px solid #ffffff26;background:#07171c9c;color:#d9e3e5;text-align:left;backdrop-filter:blur(18px);transition:background .25s var(--ease),color .25s var(--ease),transform .25s var(--ease)}.tabs button:hover:not(:disabled){transform:translateY(-2px)}.tabs button.active{background:#f8f8f6;color:#07171c}.tabs span{display:block;font-size:12px;font-weight:800;white-space:nowrap}.tabs small{display:block;margin-top:4px;color:inherit;font-size:9px;opacity:.62}.tabs i{position:absolute;right:10px;bottom:6px;left:10px;height:2px;background:#00c8f5;transform:scaleX(0);transform-origin:left;transition:transform .35s var(--ease)}.tabs button.active i{transform:scaleX(1)}.tabs.compact button{min-height:44px;padding:9px 13px;border-color:#9dacad;background:transparent;color:#526166;backdrop-filter:none}.tabs.compact button.active{border-color:#07171c;background:#07171c;color:#f8f8f6}.tabs button:focus-visible{outline:3px solid #00c8f5;outline-offset:2px}.tabs button:disabled{cursor:not-allowed;opacity:.55}@media(prefers-reduced-motion:reduce){.tabs button,.tabs i{transition:none!important}}
</style>
