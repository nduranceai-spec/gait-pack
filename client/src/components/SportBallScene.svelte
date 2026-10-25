<script lang="ts">
  import { onMount } from 'svelte';

  let container = $state<HTMLDivElement>();
  let activeStyle = $state<'soccer' | 'cyber' | 'basket'>('cyber');
  let isDragging = $state(false);

  let switchBall: (style: 'soccer' | 'cyber' | 'basket') => void = () => {};

  onMount(() => {
    let disposed = false;
    let animId = 0;

    void (async () => {
      const THREE = await import('three');
      if (!container || disposed) return;

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(40, container.clientWidth / container.clientHeight, 0.1, 100);
      camera.position.set(0, 0.2, 4.4);

      const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'high-performance' });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setSize(container.clientWidth, container.clientHeight);
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.25;
      container.appendChild(renderer.domElement);

      // Procedural Texture Generator
      function createBallTexture(type: 'soccer' | 'cyber' | 'basket') {
        const canvas = document.createElement('canvas');
        canvas.width = 1024;
        canvas.height = 512;
        const ctx = canvas.getContext('2d')!;

        if (type === 'cyber') {
          // Cyber Dark Carbon + Neon Lime Hex Grid
          ctx.fillStyle = '#0a0d0e';
          ctx.fillRect(0, 0, 1024, 512);

          // Carbon fiber pattern
          ctx.fillStyle = '#141a1c';
          for (let x = 0; x < 1024; x += 16) {
            for (let y = 0; y < 512; y += 16) {
              if ((x + y) % 32 === 0) ctx.fillRect(x, y, 8, 8);
            }
          }

          // Neon geometric kinetic lines
          ctx.strokeStyle = '#ccff00';
          ctx.lineWidth = 6;
          ctx.beginPath();
          for (let y = 64; y < 512; y += 128) {
            ctx.moveTo(0, y);
            ctx.lineTo(1024, y);
          }
          ctx.stroke();

          ctx.strokeStyle = '#00d1ff';
          ctx.lineWidth = 8;
          ctx.beginPath();
          ctx.arc(256, 256, 110, 0, Math.PI * 2);
          ctx.arc(768, 256, 110, 0, Math.PI * 2);
          ctx.stroke();

          // Brand marks
          ctx.font = '900 36px Anton, sans-serif';
          ctx.fillStyle = '#ccff00';
          ctx.fillText('KINETIC // X', 180, 265);
          ctx.fillText('9.82 m/s', 690, 265);
        } else if (type === 'soccer') {
          // Classic Match Ball with Neon Accents
          ctx.fillStyle = '#f2f4f5';
          ctx.fillRect(0, 0, 1024, 512);

          ctx.fillStyle = '#0a0a0a';
          // Pentagons / hexagons
          for (let x = 80; x < 1024; x += 190) {
            for (let y = 60; y < 512; y += 160) {
              ctx.beginPath();
              ctx.arc(x, y, 46, 0, Math.PI * 2);
              ctx.fill();
            }
          }

          ctx.strokeStyle = '#ccff00';
          ctx.lineWidth = 10;
          ctx.beginPath();
          ctx.moveTo(0, 256);
          ctx.lineTo(1024, 256);
          ctx.stroke();

          ctx.font = '800 42px Anton, sans-serif';
          ctx.fillStyle = '#00d1ff';
          ctx.fillText('FIFA SPEC', 200, 180);
          ctx.fillText('AEROSCULPT', 620, 360);
        } else {
          // Basketball
          ctx.fillStyle = '#d35400';
          ctx.fillRect(0, 0, 1024, 512);

          ctx.strokeStyle = '#111111';
          ctx.lineWidth = 14;
          ctx.beginPath();
          ctx.moveTo(0, 256);
          ctx.lineTo(1024, 256);
          ctx.moveTo(512, 0);
          ctx.lineTo(512, 512);
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(256, 256, 140, 0, Math.PI * 2);
          ctx.arc(768, 256, 140, 0, Math.PI * 2);
          ctx.stroke();

          ctx.font = '900 48px Anton, sans-serif';
          ctx.fillStyle = '#ccff00';
          ctx.fillText('SLAM // 24', 420, 275);
        }

        const texture = new THREE.CanvasTexture(canvas);
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.ClampToEdgeWrapping;
        return texture;
      }

      // Ball Group
      const ballGroup = new THREE.Group();
      scene.add(ballGroup);

      // Main Sphere
      const ballGeometry = new THREE.SphereGeometry(1.05, 64, 64);
      let currentTexture = createBallTexture(activeStyle);
      const ballMaterial = new THREE.MeshStandardMaterial({
        map: currentTexture,
        roughness: 0.32,
        metalness: 0.28,
        bumpScale: 0.05,
      });

      const ballMesh = new THREE.Mesh(ballGeometry, ballMaterial);
      ballGroup.add(ballMesh);

      // Inner glow atmosphere
      const glowGeo = new THREE.SphereGeometry(1.08, 32, 32);
      const glowMat = new THREE.MeshBasicMaterial({
        color: '#ccff00',
        transparent: true,
        opacity: 0.08,
        wireframe: true,
      });
      const glowMesh = new THREE.Mesh(glowGeo, glowMat);
      ballGroup.add(glowMesh);

      // Orbital kinetic particles ring
      const particleCount = 180;
      const particleGeo = new THREE.BufferGeometry();
      const positions = new Float32Array(particleCount * 3);
      const colors = new Float32Array(particleCount * 3);

      for (let i = 0; i < particleCount; i++) {
        const angle = (i / particleCount) * Math.PI * 2;
        const radius = 1.45 + (Math.random() - 0.5) * 0.45;
        positions[i * 3] = Math.cos(angle) * radius;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 0.4;
        positions[i * 3 + 2] = Math.sin(angle) * radius;

        // Alternate neon lime and electric cyan
        if (i % 2 === 0) {
          colors[i * 3] = 0.8; colors[i * 3 + 1] = 1.0; colors[i * 3 + 2] = 0.0;
        } else {
          colors[i * 3] = 0.0; colors[i * 3 + 1] = 0.82; colors[i * 3 + 2] = 1.0;
        }
      }

      particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      particleGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

      const particleMat = new THREE.PointsMaterial({
        size: 0.045,
        vertexColors: true,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending,
      });

      const particleRing = new THREE.Points(particleGeo, particleMat);
      particleRing.rotation.x = 0.35;
      particleRing.rotation.z = -0.2;
      ballGroup.add(particleRing);

      // Ground Shadow
      const shadowGeo = new THREE.CircleGeometry(1.3, 32);
      const shadowMat = new THREE.MeshBasicMaterial({
        color: '#000000',
        transparent: true,
        opacity: 0.55,
      });
      const shadowMesh = new THREE.Mesh(shadowGeo, shadowMat);
      shadowMesh.rotation.x = -Math.PI / 2;
      shadowMesh.position.y = -1.35;
      scene.add(shadowMesh);

      // Lights
      const ambientLight = new THREE.AmbientLight('#ffffff', 0.8);
      scene.add(ambientLight);

      const keyLight = new THREE.DirectionalLight('#ffffff', 2.4);
      keyLight.position.set(4, 5, 4);
      scene.add(keyLight);

      const neonLimeLight = new THREE.PointLight('#ccff00', 3.8, 10);
      neonLimeLight.position.set(-3, -1, 2);
      scene.add(neonLimeLight);

      const cyanRimLight = new THREE.PointLight('#00d1ff', 3.5, 10);
      cyanRimLight.position.set(3, 2, -2);
      scene.add(cyanRimLight);

      // Switch ball texture function
      switchBall = (style) => {
        activeStyle = style;
        currentTexture.dispose();
        currentTexture = createBallTexture(style);
        ballMaterial.map = currentTexture;
        ballMaterial.needsUpdate = true;
      };

      // Drag to rotate interaction
      let previousMousePosition = { x: 0, y: 0 };
      let velocity = { x: 0.006, y: 0.003 };
      let dragging = false;

      const dom = renderer.domElement;

      function onPointerDown(e: MouseEvent | TouchEvent) {
        dragging = true;
        isDragging = true;
        const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
        const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
        previousMousePosition = { x: clientX, y: clientY };
      }

      function onPointerMove(e: MouseEvent | TouchEvent) {
        if (!dragging) return;
        const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
        const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
        const deltaX = clientX - previousMousePosition.x;
        const deltaY = clientY - previousMousePosition.y;

        velocity.x = deltaX * 0.005;
        velocity.y = deltaY * 0.005;

        ballMesh.rotation.y += velocity.x;
        ballMesh.rotation.x += velocity.y;

        previousMousePosition = { x: clientX, y: clientY };
      }

      function onPointerUp() {
        dragging = false;
        isDragging = false;
      }

      dom.addEventListener('mousedown', onPointerDown);
      window.addEventListener('mousemove', onPointerMove);
      window.addEventListener('mouseup', onPointerUp);

      dom.addEventListener('touchstart', onPointerDown, { passive: true });
      window.addEventListener('touchmove', onPointerMove, { passive: true });
      window.addEventListener('touchend', onPointerUp);

      // Resize
      function onResize() {
        if (!container) return;
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
      }
      window.addEventListener('resize', onResize);

      // Animation Loop
      let clock = new THREE.Clock();

      function animate() {
        if (disposed) return;
        animId = requestAnimationFrame(animate);

        const elapsedTime = clock.getElapsedTime();

        // Damping / inertia
        if (!dragging) {
          velocity.x *= 0.96;
          velocity.y *= 0.96;
          ballMesh.rotation.y += velocity.x + 0.004;
          ballMesh.rotation.x += velocity.y;
        }

        // Floating hover
        ballGroup.position.y = Math.sin(elapsedTime * 2) * 0.08;
        glowMesh.rotation.y = -elapsedTime * 0.3;
        particleRing.rotation.y = elapsedTime * 0.5;

        renderer.render(scene, camera);
      }
      animate();

      return () => {
        disposed = true;
        cancelAnimationFrame(animId);
        window.removeEventListener('resize', onResize);
        dom.removeEventListener('mousedown', onPointerDown);
        window.removeEventListener('mousemove', onPointerMove);
        window.removeEventListener('mouseup', onPointerUp);
        dom.removeEventListener('touchstart', onPointerDown);
        window.removeEventListener('touchmove', onPointerMove);
        window.removeEventListener('touchend', onPointerUp);
        renderer.dispose();
        ballGeometry.dispose();
        ballMaterial.dispose();
        currentTexture.dispose();
        particleGeo.dispose();
        particleMat.dispose();
      };
    })();

    return () => {
      disposed = true;
      if (animId) cancelAnimationFrame(animId);
    };
  });
</script>

<div class="ball-wrapper">
  <div class="canvas-container" bind:this={container}></div>

  <!-- Style selector pills -->
  <div class="ball-controls">
    <button
      class:active={activeStyle === 'cyber'}
      onclick={() => switchBall('cyber')}
      aria-label="Cyber Ball"
    >
      <span>⚡ CYBER</span>
    </button>
    <button
      class:active={activeStyle === 'soccer'}
      onclick={() => switchBall('soccer')}
      aria-label="Match Ball"
    >
      <span>⚽ MATCH</span>
    </button>
    <button
      class:active={activeStyle === 'basket'}
      onclick={() => switchBall('basket')}
      aria-label="Slam Ball"
    >
      <span>🏀 SLAM</span>
    </button>
  </div>

  <div class="drag-hint" class:active={isDragging}>
    <span>{isDragging ? 'ROTATING 3D MODEL' : 'DRAG TO ROTATE 360°'}</span>
  </div>
</div>

<style>
  .ball-wrapper {
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 420px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .canvas-container {
    width: 100%;
    height: 100%;
    min-height: 420px;
    cursor: grab;
    touch-action: none;
  }

  .canvas-container:active {
    cursor: grabbing;
  }

  .ball-controls {
    position: absolute;
    bottom: 14px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 8px;
    z-index: 10;
    background: rgba(10, 10, 10, 0.75);
    padding: 6px 10px;
    border-radius: 9999px;
    border: 1px solid rgba(204, 255, 0, 0.25);
    backdrop-filter: blur(10px);
  }

  .ball-controls button {
    background: transparent;
    border: none;
    color: #8899a6;
    padding: 5px 12px;
    border-radius: 9999px;
    font-family: 'Anton', sans-serif;
    font-size: 13px;
    letter-spacing: 0.08em;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .ball-controls button:hover {
    color: #ffffff;
  }

  .ball-controls button.active {
    background: #ccff00;
    color: #0a0a0a;
    box-shadow: 0 0 16px rgba(204, 255, 0, 0.45);
  }

  .drag-hint {
    position: absolute;
    top: 14px;
    right: 14px;
    font-size: 11px;
    font-family: 'Oswald', sans-serif;
    letter-spacing: 0.12em;
    color: rgba(204, 255, 0, 0.75);
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(204, 255, 0, 0.2);
    padding: 4px 10px;
    border-radius: 4px;
    pointer-events: none;
    transition: all 0.2s ease;
  }

  .drag-hint.active {
    color: #00d1ff;
    border-color: #00d1ff;
  }
</style>
