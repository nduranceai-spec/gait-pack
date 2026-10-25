import { svelte } from '@sveltejs/vite-plugin-svelte';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  base: '/',
  plugins: [tailwindcss(), svelte()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    chunkSizeWarningLimit: 800,
    rollupOptions: { output: { manualChunks(id) { if (id.includes('node_modules/three/')) return 'three'; if (id.includes('@mediapipe/tasks-vision')) return 'mediapipe'; return undefined; } } },
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    // Proxy /api to the local Python backend during development only.
    // On Vercel, vercel.json routes handle this at the CDN layer.
    proxy: { '/api': 'http://127.0.0.1:8765' },
  },
  preview: {
    host: '127.0.0.1',
    port: 4173,
    strictPort: true,
    proxy: { '/api': 'http://127.0.0.1:8765' },
  },
});
