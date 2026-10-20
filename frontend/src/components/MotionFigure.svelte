<script lang="ts">
  import { onMount } from 'svelte';

  let canvas: HTMLCanvasElement;

  onMount(() => {
    const context = canvas.getContext('2d');
    if (!context) return;
    const drawing = context;
    const accent = getComputedStyle(canvas).getPropertyValue('--text').trim();
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let frameId = 0;
    let start = performance.now();

    const connections = [
      [0, 1], [1, 2], [2, 3], [1, 4], [4, 5], [5, 6], [1, 7], [7, 8],
      [8, 9], [7, 10], [10, 11], [11, 12], [3, 13], [13, 14], [14, 15],
      [3, 16], [16, 17], [17, 18],
    ];

    function draw(now: number) {
      const t = reduced ? 0 : (now - start) / 1000;
      const width = canvas.width;
      const height = canvas.height;
      drawing.clearRect(0, 0, width, height);
      const sway = Math.sin(t * 1.8) * 5;
      const stride = Math.sin(t * 2.6) * 13;
      const points = [
        [150 + sway, 42], [150 + sway, 73], [150 + sway, 115],
        [150 + sway, 157], [111 + sway, 84], [88 + sway - stride * .2, 123],
        [72 + sway - stride * .35, 164], [189 + sway, 84],
        [210 + sway + stride * .2, 123], [226 + sway + stride * .35, 164],
        [125 + sway, 157], [113 + sway + stride, 211], [98 + sway + stride, 267],
        [175 + sway, 157], [187 + sway - stride, 211], [202 + sway - stride, 267],
        [150 + sway, 74], [137 + sway, 44], [163 + sway, 44],
      ];

      drawing.lineWidth = 3;
      drawing.strokeStyle = accent;
      drawing.shadowColor = accent;
      drawing.shadowBlur = 12;
      for (const [from, to] of connections) {
        drawing.beginPath();
        drawing.moveTo(points[from][0], points[from][1]);
        drawing.lineTo(points[to][0], points[to][1]);
        drawing.stroke();
      }
      drawing.fillStyle = accent;
      for (const [x, y] of points) {
        drawing.beginPath();
        drawing.arc(x, y, 4, 0, Math.PI * 2);
        drawing.fill();
      }
      drawing.shadowBlur = 0;
      if (!reduced) frameId = requestAnimationFrame(draw);
    }

    draw(start);
    return () => cancelAnimationFrame(frameId);
  });
</script>

<canvas bind:this={canvas} width="300" height="290" aria-label="Animated gait skeleton"></canvas>
