<script lang="ts">
  import { onMount } from 'svelte';

  let { statue = false }: { statue?: boolean } = $props();

  // Change this one value to '/models/athlete-run.glb' once a licensed rigged
  // runner has been added to public/models. Keep the asset below ~3 MB.
  const ATHLETE_MODEL_URL: string | null = null;
  // A supplied GLB may either play its embedded run cycle or hold its first pose.
  const RUN_MODE: 'loop' | 'frozen' = 'loop';
  const SHOW_JOINT_GUIDES = true;

  let host = $state<HTMLDivElement>();
  let ready = $state(false);
  let unavailable = $state(false);

  onMount(() => {
    let disposed = false;
    let cleanup = () => {};

    void (async () => {
      try {
        const THREE = await import('three');
        if (!host || disposed) return;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(32, 1, .1, 100);
        camera.position.set(0, .22, 6.8);
        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'high-performance' });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(host.clientWidth, host.clientHeight, false);
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        host.appendChild(renderer.domElement);

        const matte = new THREE.MeshStandardMaterial({ color: '#07171c', roughness: .55, metalness: .54 });
        const cyan = new THREE.MeshStandardMaterial({ color: '#00c8f5', roughness: .38, metalness: .34, emissive: '#00718d', emissiveIntensity: .2 });
        const jointMaterial = new THREE.MeshBasicMaterial({ color: '#00d1ff', transparent: true, opacity: .78 });
        const jointLineMaterial = new THREE.LineBasicMaterial({ color: '#00d1ff', transparent: true, opacity: .45 });
        const runner = new THREE.Group();
        runner.rotation.y = -.34;
        scene.add(runner);

        const groundShadow = new THREE.Mesh(
          new THREE.CircleGeometry(1.24, 48),
          new THREE.MeshBasicMaterial({ color: '#07171c', transparent: true, opacity: .16, depthWrite: false }),
        );
        groundShadow.rotation.x = -Math.PI / 2;
        groundShadow.position.y = -1.08;
        groundShadow.scale.set(1.25, .46, 1);
        scene.add(groundShadow);

        const plinth = new THREE.Mesh(
          new THREE.CylinderGeometry(.68, .78, .14, 48),
          new THREE.MeshStandardMaterial({ color: '#07171c', roughness: .42, metalness: .68 }),
        );
        plinth.position.y = -1.08;
        plinth.castShadow = true;
        plinth.receiveShadow = true;
        scene.add(plinth);

        // The existing hero-orb pseudo-element supplies the original dashed ring.
        // Keeping it outside the WebGL canvas preserves the landing composition exactly.

        const trails = new THREE.Group();
        for (let index = 0; index < 5; index += 1) {
          const geometry = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(-1.85 - index * .13, .26 + index * .22, -.45),
            new THREE.Vector3(-.72 - index * .06, .26 + index * .22, -.45),
          ]);
          const line = new THREE.Line(geometry, new THREE.LineBasicMaterial({ color: '#00c8f5', transparent: true, opacity: .14 + index * .04 }));
          trails.add(line);
        }
        scene.add(trails);

        scene.add(new THREE.HemisphereLight('#ffffff', '#8acfe0', 1.55));
        const key = new THREE.DirectionalLight('#ffffff', 2.75); key.position.set(3.4, 5, 4.6); key.castShadow = true; key.shadow.mapSize.set(512, 512); scene.add(key);
        const rim = new THREE.DirectionalLight('#00c8f5', 2.8); rim.position.set(-4, 1.5, -3); scene.add(rim);
        const fill = new THREE.PointLight('#bceefa', 3.2, 10); fill.position.set(0, -1.5, 3); scene.add(fill);

        let mixer: InstanceType<typeof THREE.AnimationMixer> | null = null;
        let procedural = true;
        let leftHip: InstanceType<typeof THREE.Group> | null = null;
        let rightHip: InstanceType<typeof THREE.Group> | null = null;
        let leftKnee: InstanceType<typeof THREE.Group> | null = null;
        let rightKnee: InstanceType<typeof THREE.Group> | null = null;
        let leftShoulder: InstanceType<typeof THREE.Group> | null = null;
        let rightShoulder: InstanceType<typeof THREE.Group> | null = null;
        let leftElbow: InstanceType<typeof THREE.Group> | null = null;
        let rightElbow: InstanceType<typeof THREE.Group> | null = null;
        const animatedBody = new THREE.Group();
        runner.add(animatedBody);

        const dot = (group: InstanceType<typeof THREE.Group>, x: number, y: number, z = 0) => {
          if (!SHOW_JOINT_GUIDES) return;
          const marker = new THREE.Mesh(new THREE.SphereGeometry(.042, 10, 10), jointMaterial);
          marker.position.set(x, y, z);
          group.add(marker);
        };
        const segment = (pivot: InstanceType<typeof THREE.Group>, length: number, radius: number, material: InstanceType<typeof THREE.MeshStandardMaterial>, accent = false) => {
          const limb = new THREE.Mesh(new THREE.CapsuleGeometry(radius, Math.max(.01, length - radius * 2), 8, 12), material);
          limb.position.y = -length / 2;
          limb.castShadow = true;
          limb.receiveShadow = true;
          pivot.add(limb);
          if (SHOW_JOINT_GUIDES) {
            const guide = new THREE.Line(
              new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, radius + .01), new THREE.Vector3(0, -length, radius + .01)]),
              jointLineMaterial,
            );
            pivot.add(guide);
          }
          if (accent) {
            const stripe = new THREE.Mesh(new THREE.BoxGeometry(radius * 1.7, length * .18, radius * 1.78), cyan);
            stripe.position.y = -length * .67;
            pivot.add(stripe);
          }
        };
        const chain = (x: number, y: number, upper: number, lower: number, upperRadius: number, lowerRadius: number, arm = false) => {
          const root = new THREE.Group(); root.position.set(x, y, 0); animatedBody.add(root); dot(root, 0, 0);
          segment(root, upper, upperRadius, matte, true);
          const joint = new THREE.Group(); joint.position.y = -upper; root.add(joint); dot(joint, 0, 0);
          segment(joint, lower, lowerRadius, matte, !arm);
          const end = new THREE.Group(); end.position.y = -lower; joint.add(end); dot(end, 0, 0);
          return { root, joint, end };
        };
        const buildProceduralAthlete = () => {
          const torso = new THREE.Mesh(new THREE.CapsuleGeometry(.34, .72, 10, 16), matte);
          torso.position.set(0, .7, 0); torso.rotation.x = -.16; torso.castShadow = true; animatedBody.add(torso);
          const chestPanel = new THREE.Mesh(new THREE.BoxGeometry(.34, .4, .37), cyan);
          chestPanel.position.set(0, .75, .27); chestPanel.rotation.x = -.16; animatedBody.add(chestPanel);
          const head = new THREE.Mesh(new THREE.SphereGeometry(.22, 20, 16), matte);
          head.position.set(0, 1.45, -.08); head.castShadow = true; animatedBody.add(head);
          const visor = new THREE.Mesh(new THREE.SphereGeometry(.14, 16, 12), cyan);
          visor.scale.set(1.18, .52, .28); visor.position.set(0, 1.47, .145); animatedBody.add(visor);
          const leftArm = chain(-.39, 1.05, .48, .43, .095, .072, true);
          const rightArm = chain(.39, 1.05, .48, .43, .095, .072, true);
          const leftLeg = chain(-.18, .28, .66, .61, .14, .105);
          const rightLeg = chain(.18, .28, .66, .61, .14, .105);
          const foot = (end: InstanceType<typeof THREE.Group>) => {
            const shoe = new THREE.Mesh(new THREE.BoxGeometry(.19, .1, .42), cyan);
            shoe.position.set(0, -.03, .15); shoe.castShadow = true; end.add(shoe);
          };
          foot(leftLeg.end); foot(rightLeg.end);
          leftHip = leftLeg.root; rightHip = rightLeg.root; leftKnee = leftLeg.joint; rightKnee = rightLeg.joint;
          leftShoulder = leftArm.root; rightShoulder = rightArm.root; leftElbow = leftArm.joint; rightElbow = rightArm.joint;
        };
        const setBrandMaterials = (object: InstanceType<typeof THREE.Object3D>) => {
          object.traverse((node) => {
            if (!(node instanceof THREE.Mesh)) return;
            const name = `${node.name} ${(node.material as { name?: string }).name ?? ''}`.toLowerCase();
            const accent = /shoe|sneaker|sole|sleeve|stripe|accent|seam|trim/.test(name);
            const existing = Array.isArray(node.material) ? node.material[0] : node.material;
            const material = new THREE.MeshStandardMaterial({
              color: accent ? '#00c8f5' : '#07171c',
              roughness: accent ? .38 : .55,
              metalness: accent ? .34 : .54,
              emissive: accent ? '#006a84' : '#000000',
              emissiveIntensity: accent ? .16 : 0,
              map: (existing as { map?: unknown }).map as never ?? null,
              normalMap: (existing as { normalMap?: unknown }).normalMap as never ?? null,
            });
            node.material = material;
            node.castShadow = true;
            node.receiveShadow = true;
          });
        };
        const loadGlb = async () => {
          if (!ATHLETE_MODEL_URL) return false;
          try {
            const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
            const loader = new GLTFLoader();
            const gltf = await loader.loadAsync(ATHLETE_MODEL_URL);
            const model = gltf.scene;
            setBrandMaterials(model);
            const box = new THREE.Box3().setFromObject(model);
            const size = box.getSize(new THREE.Vector3());
            const centre = box.getCenter(new THREE.Vector3());
            const scale = 2.45 / Math.max(size.y, .01);
            model.scale.setScalar(scale);
            model.position.set(-centre.x * scale, -box.min.y * scale - 1.08, -centre.z * scale);
            animatedBody.add(model);
            if (gltf.animations.length) {
              mixer = new THREE.AnimationMixer(model);
              const action = mixer.clipAction(gltf.animations[0]);
              action.reset();
              if (RUN_MODE === 'loop') action.play();
              else action.paused = true;
            }
            procedural = false;
            return true;
          } catch (error) {
            console.warn('GAIT athlete GLB could not be loaded; using the procedural runner.', error);
            return false;
          }
        };
        if (!(await loadGlb())) buildProceduralAthlete();

        const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        let reduce = reducedMotion.matches;
        const onMotionChange = () => { reduce = reducedMotion.matches; };
        reducedMotion.addEventListener('change', onMotionChange);
        let visible = true;
        let pageVisible = !document.hidden;
        const clock = new THREE.Clock();
        let targetYaw = -.34;
        let yaw = targetYaw;
        let velocity = 0;
        let pointerX = 0;
        let parallax = 0;
        let dragging = false;
        let lastX = 0;
        const onPointerDown = (event: PointerEvent) => { dragging = true; lastX = event.clientX; host?.setPointerCapture(event.pointerId); };
        const onPointerMove = (event: PointerEvent) => {
          const bounds = host?.getBoundingClientRect();
          if (bounds) pointerX = (event.clientX - bounds.left) / Math.max(bounds.width, 1) - .5;
          if (!dragging) return;
          const delta = event.clientX - lastX;
          targetYaw += delta * .012;
          velocity = delta * .0013;
          lastX = event.clientX;
        };
        const onPointerUp = () => { dragging = false; };
        host.addEventListener('pointerdown', onPointerDown);
        host.addEventListener('pointermove', onPointerMove);
        window.addEventListener('pointerup', onPointerUp);
        const resize = () => {
          if (!host) return;
          const { width, height } = host.getBoundingClientRect();
          renderer.setSize(width, height, false);
          camera.aspect = width / Math.max(height, 1);
          camera.updateProjectionMatrix();
        };
        const resizer = new ResizeObserver(resize);
        resizer.observe(host);
        let frame = 0;
        let loopRunning = false;
        const render = () => {
          if (!visible || !pageVisible) { loopRunning = false; return; }
          const delta = Math.min(clock.getDelta(), .05);
          const elapsed = clock.elapsedTime;
            if (!reduce) {
            if (procedural && !statue) {
              const phase = elapsed * 8.4;
              const stride = Math.sin(phase);
              leftHip!.rotation.x = stride * .78; rightHip!.rotation.x = -stride * .78;
              leftKnee!.rotation.x = Math.max(0, -stride) * .95; rightKnee!.rotation.x = Math.max(0, stride) * .95;
              leftShoulder!.rotation.x = -stride * .72; rightShoulder!.rotation.x = stride * .72;
              leftElbow!.rotation.x = Math.max(0, stride) * .48; rightElbow!.rotation.x = Math.max(0, -stride) * .48;
              animatedBody.rotation.z = Math.sin(phase * 2) * .025;
              trails.children.forEach((line, index) => { line.position.x = Math.sin(elapsed * 2.1 + index) * .12; });
            }
            if (!statue && RUN_MODE === 'loop') mixer?.update(delta);
          }
          if (!dragging) {
            targetYaw += velocity;
            velocity *= .92;
            if (Math.abs(velocity) < .00015) targetYaw += reduce ? .0002 : .0015;
          }
          yaw += (targetYaw - yaw) * .065;
          parallax += (pointerX * .09 - parallax) * .055;
          runner.rotation.y = yaw;
          runner.rotation.z = parallax;
          renderer.render(scene, camera);
          frame = requestAnimationFrame(render);
        };
        const resumeRender = () => {
          if (!loopRunning && visible && pageVisible) {
            loopRunning = true;
            clock.getDelta();
            frame = requestAnimationFrame(render);
          }
        };
        const observer = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; resumeRender(); }, { threshold: .05 });
        observer.observe(host);
        const onVisibility = () => { pageVisible = !document.hidden; resumeRender(); };
        document.addEventListener('visibilitychange', onVisibility);
        ready = true;
        resumeRender();

        const disposeObject = (object: InstanceType<typeof THREE.Object3D>) => {
          const geometries = new Set<object>();
          const materials = new Set<object>();
          const textures = new Set<object>();
          object.traverse((node) => {
            const renderable = node as InstanceType<typeof THREE.Object3D> & { geometry?: { dispose: () => void }; material?: InstanceType<typeof THREE.Material> | InstanceType<typeof THREE.Material>[] };
            if (renderable.geometry && !geometries.has(renderable.geometry)) { geometries.add(renderable.geometry); renderable.geometry.dispose(); }
            const nodeMaterials = renderable.material ? (Array.isArray(renderable.material) ? renderable.material : [renderable.material]) : [];
            nodeMaterials.forEach((material) => {
              if (materials.has(material)) return;
              materials.add(material);
              Object.values(material).forEach((value) => {
                if (value && typeof value === 'object' && 'isTexture' in value && !textures.has(value)) { textures.add(value); (value as InstanceType<typeof THREE.Texture>).dispose(); }
              });
              material.dispose();
            });
          });
        };
        cleanup = () => {
          cancelAnimationFrame(frame);
          resizer.disconnect(); observer.disconnect();
          reducedMotion.removeEventListener('change', onMotionChange);
          document.removeEventListener('visibilitychange', onVisibility);
          host?.removeEventListener('pointerdown', onPointerDown);
          host?.removeEventListener('pointermove', onPointerMove);
          window.removeEventListener('pointerup', onPointerUp);
          mixer?.stopAllAction();
          disposeObject(scene);
          renderer.dispose();
          renderer.forceContextLoss();
          renderer.domElement.remove();
        };
      } catch (error) {
        console.warn('GAIT athlete scene is unavailable.', error);
        unavailable = true;
      }
    })();

    return () => { disposed = true; cleanup(); };
  });
</script>

<div class="ball-host athlete-host" bind:this={host} role="img" aria-label="Interactive three dimensional running athlete">
  {#if !ready || unavailable}<div class="athlete-fallback" aria-hidden="true"><i></i><span></span></div>{/if}
</div>

<style>
  .athlete-host{position:relative;width:100%;height:100%}.athlete-host :global(canvas){position:relative;z-index:1;width:100%;height:100%}.athlete-fallback{position:absolute;inset:8%;display:grid;place-items:center;border:1px dashed #80cfe0;border-radius:50%;opacity:.55}.athlete-fallback i{display:block;width:24%;aspect-ratio:1;border:2px solid #07171c;border-radius:50%;box-shadow:0 42px 0 -7px #07171c,0 80px 0 -9px #07171c}.athlete-fallback span{position:absolute;bottom:15%;width:42%;height:7%;border-radius:50%;background:#07171c33;filter:blur(5px)}
</style>
