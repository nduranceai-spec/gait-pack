<script lang="ts">
  let {
    label,
    tone = 'mint',
    pulse = false,
  }: {
    label: string;
    tone?: 'mint' | 'violet' | 'gold' | 'muted';
    pulse?: boolean;
  } = $props();
</script>

<span class="status-pill {tone}">
  <span class:pulse class="status-dot"></span>
  {label}
</span>
