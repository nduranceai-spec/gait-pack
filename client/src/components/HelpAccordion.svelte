<script lang="ts">
  let { items }: { items: { question: string; answer: string }[] } = $props();
</script>

<div class="help-accordion">
  {#each items as item}
    <details>
      <summary>{item.question}<span class="disclosure-mark" aria-hidden="true">+</span></summary>
      <p>{item.answer}</p>
    </details>
  {/each}
</div>
